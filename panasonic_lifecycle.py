"""Exact Panasonic product-page evidence; presence alone is not lifecycle proof."""
import hashlib
import re
from datetime import datetime
from html.parser import HTMLParser

ORIGIN = 'https://industrial.panasonic.com'
PATH = '/ww/products/pt/general-purpose-chip-resistors/models/'
PARSER = 'panasonic-exact-product-v1'
STATUS = 'NRND（不推荐新设计）'


def official_model(model):
    """Only the observed optional ERJ hyphen, not arbitrary punctuation removal."""
    if not isinstance(model,str) or not re.fullmatch(r'ERJ-?[A-Z0-9]{5,24}',model):
        raise ValueError('Not an exact supported Panasonic ordering code')
    return model.replace('ERJ-','ERJ',1)


class ProductPage(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.headings=[]; self.part=''; self.statuses=[]; self.canonicals=[]
        self.in_heading=self.in_part=self.in_status=False

    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if tag=='link' and attrs.get('rel')=='canonical': self.canonicals.append(attrs.get('href',''))
        if tag=='h1': self.in_heading=True; self.headings.append('')
        if tag=='h3' and attrs.get('data-drupal-selector')=='edit-product-number': self.in_part=True
        if tag in {'div','span'} and self.in_part: self.part+=' '
        if tag=='span' and self.in_part and attrs.get('data-drupal-selector')=='edit-status':
            self.in_status=True; self.statuses.append('')

    def handle_data(self,text):
        if self.in_heading: self.headings[-1]+=text
        if self.in_part: self.part+=text
        if self.in_status: self.statuses[-1]+=text

    def handle_endtag(self,tag):
        if tag=='h1': self.in_heading=False
        if tag=='h3': self.in_part=False
        if tag=='span': self.in_status=False


def product_record(source,url,model,checked_at):
    official=official_model(model)
    if url!=ORIGIN+PATH+official: raise ValueError('Not the exact official product URL')
    if datetime.fromisoformat(checked_at).tzinfo is None: raise ValueError('Timezone required')
    page=ProductPage(); page.feed(source)
    if (page.canonicals!=[url] or len(page.headings)!=1
        or not page.headings[0].startswith(official+' (NRFND) : ')
        or [s.strip() for s in page.statuses]!=['NRFND']
        or page.part.split()!=['Parts','no',official,'NRFND']):
        return None
    return dict(manufacturer='panasonic',model=model,official_model=official,
                status=STATUS,raw_status='NRFND',source=url,checked_at=checked_at,
                source_sha256=hashlib.sha256(source.encode('utf-8')).hexdigest(),parser=PARSER)


def valid_record(record):
    try:
        official=official_model(record['model'])
        return (record.get('manufacturer')=='panasonic' and record.get('parser')==PARSER
                and record.get('official_model')==official and record.get('status')==STATUS
                and record.get('raw_status')=='NRFND' and record.get('source')==ORIGIN+PATH+official
                and datetime.fromisoformat(record['checked_at']).tzinfo is not None
                and bool(re.fullmatch('[0-9a-f]{64}',record.get('source_sha256','')))
                and not record.get('parameters'))
    except (KeyError,ValueError,TypeError):
        return False
