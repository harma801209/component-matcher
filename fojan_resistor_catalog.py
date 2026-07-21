from __future__ import annotations

from copy import deepcopy


NORMAL_POWER = {
    "0201": "1/20W",
    "0402": "1/16W",
    "0603": "1/10W",
    "0805": "1/8W",
    "1206": "1/4W",
    "1210": "1/2W",
    "1812": "3/4W",
    "2010": "3/4W",
    "2512": "1W",
}

NORMAL_VOLTAGE = {
    "0201": "25",
    "0402": "50",
    "0603": "75",
    "0805": "150",
    "1206": "200",
    "1210": "200",
    "1812": "200",
    "2010": "200",
    "2512": "200",
}

HIGH_POWER = {
    "0402": "1/10W",
    "0603": "1/5W",
    "0805": "1/4W",
    "1206": "1/2W",
    "1210": "3/4W",
    "1812": "1W",
    "2010": "1W",
    "2512": "2W",
}

ULTRA_POWER = {
    "0402": "1/5W",
    "0603": "1/3W",
    "0805": "1/2W",
    "1206": "3/4W",
    "1210": "1W",
    "2010": "1.5W",
    "2512": "3W",
}

ULTRA_VOLTAGE = {
    "0402": "50",
    "0603": "150",
    "0805": "200",
    "1206": "200",
    "1210": "200",
    "2010": "200",
    "2512": "250",
}

HIGH_VOLTAGE = {
    "0603": "350",
    "0805": "400",
    "1206": "500",
    "1210": "500",
    "1812": "500",
    "2010": "500",
    "2512": "500",
}

WIDE_POWER = {"0612": "0.75W", "1020": "1W", "1225": "2W"}
WIDE_HIGH_POWER = {"0612": "1.5W", "1020": "2W", "1225": "3W"}
WIDE_VOLTAGE = {"0612": "200", "1020": "200", "1225": "200"}

ARRAY_POWER = {
    "022R": "1/20W",
    "042R": "1/16W",
    "062R": "1/10W",
    "024R": "1/20W",
    "044R": "1/16W",
    "064R": "1/10W",
}

ARRAY_VOLTAGE = {
    "022R": "15",
    "042R": "50",
    "062R": "50",
    "024R": "12.5",
    "044R": "25",
    "064R": "50",
}

ALL_STANDARD_TOLERANCES = ("0.05", "0.1", "0.25", "0.5", "1", "5")
PRECISION_TOLERANCES = ("0.01", "0.05", "0.1", "0.25", "0.5", "1")
LOW_OHM_TOLERANCES = ("0.1", "0.25", "0.5", "1", "2", "5")


def _size_limits(power_map, minimum=1.0, maximum=10_000_000.0, *, min_0201=None):
    result = {}
    for size, power in power_map.items():
        result[size] = {
            "power": power,
            "voltage": NORMAL_VOLTAGE.get(size, ""),
            "min_ohm": min_0201 if size == "0201" and min_0201 is not None else minimum,
            "max_ohm": maximum,
        }
    return result


def _series(
    description,
    special_use,
    sizes,
    source,
    *,
    component_type="厚膜电阻",
    tolerances=ALL_STANDARD_TOLERANCES,
    model_prefix="",
    suffixes=("TS",),
    model_size_by_size=None,
    value_encoding="standard",
    series_display="",
    material="",
):
    return {
        "description": description,
        "special_use": special_use,
        "component_type": component_type,
        "tolerances": tuple(tolerances),
        "model_prefix": model_prefix,
        "suffixes": tuple(suffixes),
        "model_size_by_size": dict(model_size_by_size or {}),
        "value_encoding": value_encoding,
        "series_display": series_display,
        "material": material or ("金属膜" if component_type == "薄膜电阻" else "厚膜"),
        "sizes": deepcopy(sizes),
        "source": source,
    }


FOJAN_SPECIAL_RESISTOR_SERIES = {
    "FQA": _series(
        "车规厚膜贴片排列电阻",
        "车规 | 排阻 | 无卤",
        {
            size: {
                "power": power,
                "voltage": ARRAY_VOLTAGE[size],
                "min_ohm": 10.0,
                "max_ohm": 1_000_000.0,
            }
            for size, power in ARRAY_POWER.items()
        },
        "FQA系列车规厚膜片式排列电阻.pdf",
        tolerances=("1", "5"),
        value_encoding="e24_3digit",
    ),
    "FAR": _series(
        "抗硫化车规厚膜贴片排列电阻",
        "车规 | 抗硫化 | 排阻 | 无卤",
        {
            size: {
                "power": power,
                "voltage": ARRAY_VOLTAGE[size],
                "min_ohm": 10.0,
                "max_ohm": 1_000_000.0,
            }
            for size, power in ARRAY_POWER.items()
        },
        "FAR系列抗硫化车规排阻厚膜片式电阻.pdf",
        tolerances=("1", "5"),
        value_encoding="e24_3digit",
    ),
    "FRQ": _series(
        "车规级厚膜贴片电阻",
        "车规 | 无卤",
        _size_limits(NORMAL_POWER, min_0201=10.0),
        "FRQ系列常用车规厚膜电阻.pdf",
    ),
    "FRR": _series(
        "车规抗硫化厚膜贴片电阻",
        "车规 | 抗硫化 | 无卤",
        _size_limits(NORMAL_POWER, minimum=0.1, min_0201=10.0),
        "FRR系列车规抗硫化厚膜电阻.pdf",
    ),
    "FRN": _series(
        "汽车级高品质抗硫化厚膜贴片电阻",
        "车规 | 抗硫化 | 无卤",
        _size_limits(NORMAL_POWER, min_0201=10.0),
        "FRN系列汽车级高品质抗硫化厚膜片式电阻.pdf",
    ),
    "FQS": _series(
        "车规抗浪涌抗硫化厚膜贴片电阻",
        "车规 | 抗浪涌 | 抗硫化 | 无卤",
        _size_limits({key: value for key, value in NORMAL_POWER.items() if key not in {"0201", "0402"}}),
        "FQS系列抗浪涌车规厚膜片式电阻.pdf",
        tolerances=("1", "5"),
    ),
    "FRS": _series(
        "抗浪涌厚膜贴片电阻",
        "抗浪涌 | 无卤",
        _size_limits({key: value for key, value in NORMAL_POWER.items() if key not in {"0201", "0402"}}),
        "FRS系列抗浪涌厚膜片式电阻.pdf",
        tolerances=("1", "5"),
    ),
    "FRV": _series(
        "高压厚膜贴片电阻",
        "高压 | 无卤",
        {
            size: {"power": NORMAL_POWER[size], "voltage": voltage, "min_ohm": 47.0, "max_ohm": 10_000_000.0}
            for size, voltage in HIGH_VOLTAGE.items()
        },
        "FRV系列高压厚膜片式电阻.pdf",
        tolerances=("1", "5"),
    ),
    "FQV": _series(
        "车规高压抗硫化厚膜贴片电阻",
        "车规 | 高压 | 抗硫化 | 无卤",
        {
            size: {"power": NORMAL_POWER[size], "voltage": voltage, "min_ohm": 47.0, "max_ohm": 10_000_000.0}
            for size, voltage in HIGH_VOLTAGE.items()
        },
        "FQV系列高压车规厚膜片式电阻.pdf",
        tolerances=("1", "5"),
    ),
    "FRE": _series(
        "抗静电厚膜贴片电阻",
        "防静电 | 无卤",
        _size_limits({key: value for key, value in NORMAL_POWER.items() if key in {"0201", "0402", "0603", "0805", "1206", "1210"}}, min_0201=10.0),
        "FRE系列抗静电厚膜片式电阻.pdf",
        tolerances=("1", "5"),
    ),
    "FRG": _series(
        "高阻值厚膜贴片电阻",
        "高阻值 | 无卤",
        _size_limits({key: value for key, value in NORMAL_POWER.items() if key != "0201"}, minimum=10_000_000.0, maximum=100_000_000.0),
        "FRG系列高阻值厚膜片式电阻.pdf",
        tolerances=("1", "5"),
    ),
    "FRD": _series(
        "LED抗弯折厚膜贴片电阻",
        "LED | 抗弯折 | 无卤",
        _size_limits({"0805": NORMAL_POWER["0805"], "1206": NORMAL_POWER["1206"]}),
        "FRD系列LED厚膜片式电阻.pdf",
        tolerances=("1", "5"),
    ),
    "FRZ": _series(
        "无磁厚膜贴片电阻",
        "无磁 | 无卤",
        _size_limits({key: NORMAL_POWER[key] for key in ("0603", "0805", "1206")}),
        "FRZ系列无磁厚膜片式电阻.pdf",
        tolerances=("1", "5"),
    ),
    "FRP": _series(
        "高功率厚膜贴片电阻",
        "高功率 | 无卤",
        _size_limits(HIGH_POWER),
        "FRP系列高功率厚膜片式电阻.pdf",
        tolerances=("0.5", "1", "5"),
    ),
    "FPR": _series(
        "车规高功率抗硫化厚膜贴片电阻",
        "车规 | 高功率 | 抗硫化 | 无卤",
        _size_limits({key: value for key, value in HIGH_POWER.items() if key != "0402"}, minimum=0.1),
        "FPR系列高功率车规抗硫化厚膜电阻.pdf",
        tolerances=("1", "5"),
    ),
    "FQP": _series(
        "车规高功率厚膜贴片电阻",
        "车规 | 高功率 | 无卤",
        _size_limits({key: value for key, value in HIGH_POWER.items() if key != "0402"}, minimum=0.1),
        "FQP系列高功率车规厚膜电阻.pdf",
        tolerances=("1", "5"),
    ),
    "FPS": _series(
        "高功率抗浪涌厚膜贴片电阻",
        "高功率 | 抗浪涌 | 无卤",
        _size_limits({key: value for key, value in HIGH_POWER.items() if key != "0402"}),
        "FPS系列高功率抗浪涌厚膜片式电阻.pdf",
        tolerances=("1", "5"),
    ),
    "FCP": _series(
        "超高功率厚膜贴片电阻",
        "高功率 | 无卤",
        {
            size: {"power": power, "voltage": ULTRA_VOLTAGE[size], "min_ohm": 1.0, "max_ohm": 10_000_000.0}
            for size, power in ULTRA_POWER.items()
        },
        "FCP系列常规超高功率厚膜片式电阻.pdf",
        tolerances=("1", "5"),
    ),
    "FUP": _series(
        "车规超高功率厚膜贴片电阻",
        "车规 | 高功率 | 抗硫化 | 无卤",
        {
            size: {"power": power, "voltage": ULTRA_VOLTAGE[size], "min_ohm": 1.0, "max_ohm": 10_000_000.0}
            for size, power in ULTRA_POWER.items()
        },
        "FUP系列车规超高功率厚膜片式电阻.pdf",
        tolerances=("1", "5"),
    ),
    "FRC-X": _series(
        "低温漂厚膜贴片电阻",
        "低温漂 | 无卤",
        _size_limits({key: value for key, value in NORMAL_POWER.items() if key != "0201"}),
        "FRC-X系列常规低温漂厚膜片式电阻.pdf",
        model_prefix="FRC",
        suffixes=("TSX",),
    ),
    "FRP-X": _series(
        "低温漂高功率厚膜贴片电阻",
        "低温漂 | 高功率 | 无卤",
        _size_limits(HIGH_POWER),
        "FRP-X系列低温漂高功率厚膜片式电阻.pdf",
        tolerances=("0.5", "1", "5"),
        model_prefix="FRP",
        suffixes=("TSX",),
    ),
    "FRB": _series(
        "低温漂厚膜贴片电阻",
        "低温漂 | 无卤",
        _size_limits(NORMAL_POWER, min_0201=10.0),
        "FRB系列常规低TCR厚膜片式电阻.pdf",
        tolerances=("0.1", "0.25", "0.5", "1", "5"),
    ),
    "FRH": _series(
        "高精度厚膜贴片电阻",
        "高精度 | 无卤",
        _size_limits({key: value for key, value in NORMAL_POWER.items() if key != "0201"}),
        "FRH系列高精度厚膜片式电阻器.pdf",
        tolerances=("0.1", "0.25", "0.5"),
    ),
    "FRT": _series(
        "高精度低温漂薄膜贴片电阻",
        "高精度 | 低温漂 | 无卤",
        {
            size: {
                "power": NORMAL_POWER[size],
                "voltage": NORMAL_VOLTAGE[size],
                "min_ohm": 2.2,
                "max_ohm": maximum,
            }
            for size, maximum in {
                "0402": 220_000.0,
                "0603": 680_000.0,
                "0805": 1_000_000.0,
                "1206": 1_500_000.0,
                "1210": 1_000_000.0,
                "2010": 1_000_000.0,
                "2512": 1_000_000.0,
            }.items()
        },
        "FRT 系列薄膜片式电阻.pdf",
        component_type="薄膜电阻",
        tolerances=("0.05", "0.1", "0.25", "0.5", "1"),
        suffixes=("TSV",),
    ),
    "FTH": _series(
        "超高精度低温漂薄膜贴片电阻",
        "高精度 | 低温漂 | 无卤",
        _size_limits({key: value for key, value in NORMAL_POWER.items() if key not in {"0201", "1812"}}, minimum=2.2, maximum=1_500_000.0),
        "FTH 系列高精度薄膜片式电阻.pdf",
        component_type="薄膜电阻",
        tolerances=PRECISION_TOLERANCES,
        suffixes=("TSX",),
    ),
    "FQT": _series(
        "车规高精度低温漂薄膜贴片电阻",
        "车规 | 高精度 | 低温漂 | 无卤",
        _size_limits({key: value for key, value in NORMAL_POWER.items() if key not in {"0201", "1812"}}, minimum=2.2, maximum=1_500_000.0),
        "FQT系列汽车级薄膜片式电阻.pdf",
        component_type="薄膜电阻",
        tolerances=("0.05", "0.1", "0.25", "0.5", "1"),
        suffixes=("TSX",),
    ),
    "FTR": _series(
        "车规抗硫化高精度低温漂薄膜贴片电阻",
        "车规 | 抗硫化 | 高精度 | 低温漂 | 无卤",
        _size_limits({key: value for key, value in NORMAL_POWER.items() if key != "0201"}, minimum=2.2, maximum=1_500_000.0),
        "FTR系列汽车级抗硫化薄膜片式电阻.pdf",
        component_type="薄膜电阻",
        tolerances=("0.1", "0.25", "0.5", "1"),
        suffixes=("TSX",),
    ),
    "FRL": _series(
        "低阻值厚膜贴片电阻",
        "低阻值 | 无卤",
        _size_limits({key: value for key, value in NORMAL_POWER.items() if key != "0201"}, minimum=0.1, maximum=0.99),
        "FRL系列常规低阻厚膜片式电阻.pdf",
        tolerances=("1", "2", "5"),
    ),
    "FNL": _series(
        "低阻低温漂厚膜贴片电阻",
        "低阻值 | 低温漂 | 无卤",
        {
            size: {"power": power, "voltage": NORMAL_VOLTAGE.get(size, ""), "min_ohm": 0.1 if size in {"0402", "0603"} else 0.05, "max_ohm": 0.99}
            for size, power in NORMAL_POWER.items() if size != "0201"
        },
        "FNL系列低阻低温漂厚膜片式电阻.pdf",
        tolerances=("1", "2", "5"),
    ),
    "FRJ": _series(
        "低阻低温漂厚膜贴片电阻",
        "低阻值 | 低温漂 | 无卤",
        _size_limits({key: value for key, value in NORMAL_POWER.items() if key != "0201"}, minimum=0.1, maximum=0.9),
        "FRJ系列低阻低TCR厚膜片式电阻.pdf",
        tolerances=("0.1", "0.25", "0.5", "1", "5"),
    ),
    "FRL-L": _series(
        "低阻低温漂厚膜贴片电阻",
        "低阻值 | 低温漂 | 无卤",
        {
            size: {"power": power, "voltage": NORMAL_VOLTAGE.get(size, ""), "min_ohm": 0.1 if size in {"0402", "0603"} else 0.05, "max_ohm": 0.99}
            for size, power in NORMAL_POWER.items() if size not in {"0201", "1812"}
        },
        "FRL-L系列低阻低温漂厚膜片式电阻.pdf",
        tolerances=("1", "2", "5"),
        model_prefix="FRL",
        suffixes=("TSL",),
    ),
    "FQL": _series(
        "车规抗硫化低阻厚膜贴片电阻",
        "车规 | 抗硫化 | 低阻值 | 无卤",
        {
            size: {"power": power, "voltage": NORMAL_VOLTAGE.get(size, ""), "min_ohm": 0.1 if size == "0402" else 0.05, "max_ohm": 0.9}
            for size, power in NORMAL_POWER.items() if size != "0201"
        },
        "FQL系列低阻车规厚膜片式电阻.pdf",
        tolerances=("1", "5"),
    ),
    "FQL-L": _series(
        "车规低阻低温漂厚膜贴片电阻",
        "车规 | 低阻值 | 低温漂 | 无卤",
        {
            size: {"power": power, "voltage": NORMAL_VOLTAGE.get(size, ""), "min_ohm": 0.1 if size in {"0402", "0603"} else 0.05, "max_ohm": 0.99}
            for size, power in NORMAL_POWER.items() if size not in {"0201", "1812"}
        },
        "FQL-L系列汽车级低阻低温漂厚膜片式电阻.pdf",
        tolerances=("1", "2", "5"),
        model_prefix="FQL",
        suffixes=("TSL",),
    ),
    "FQL-TCR": _series(
        "车规低阻低TCR金属膜贴片电阻",
        "车规 | 低阻值 | 低温漂 | 无卤",
        {
            size: {
                "power": power,
                "voltage": NORMAL_VOLTAGE.get(size, ""),
                "min_ohm": 0.05 if size in {"0402", "0603"} else 0.039,
                "max_ohm": 10.0,
            }
            for size, power in NORMAL_POWER.items()
            if size in {"0402", "0603", "0805", "1206", "1210", "2010", "2512"}
        },
        "FQL 系列车规低阻低TCR厚膜片式电阻.pdf",
        component_type="薄膜电阻",
        tolerances=("0.25", "0.5", "1", "5"),
        model_prefix="FQL",
        suffixes=("TSW",),
        series_display="FQL",
        material="金属膜",
    ),
    "FQL-WIDE": _series(
        "车规低阻宽电极厚膜贴片电阻",
        "车规 | 低阻值 | 宽端子 | 无卤",
        {
            "0508": {"power": "1W", "voltage": "200", "min_ohm": 0.01, "max_ohm": 2.0},
            "0612": {"power": "1W", "voltage": "200", "min_ohm": 0.01, "max_ohm": 2.0},
            "1020": {"power": "2W", "voltage": "200", "min_ohm": 0.01, "max_ohm": 2.0},
            "1225": {"power": "3W", "voltage": "200", "min_ohm": 0.01, "max_ohm": 2.0},
        },
        "FQL 系列车规低阻宽电极厚膜片式电阻.pdf",
        tolerances=("0.5", "1", "2", "5"),
        model_prefix="FQL",
        suffixes=("TSR",),
        model_size_by_size={"0508": "071W", "0612": "091W", "1020": "132W", "1225": "143W"},
        series_display="FQL",
    ),
    "FPL": _series(
        "高功率低阻厚膜贴片电阻",
        "高功率 | 低阻值 | 无卤",
        {
            size: {"power": power, "voltage": NORMAL_VOLTAGE.get(size, ""), "min_ohm": 0.1 if size in {"0402", "0603"} else 0.05, "max_ohm": 0.99}
            for size, power in HIGH_POWER.items()
        },
        "FPL系列高功率低阻厚膜片式电阻.pdf",
        tolerances=("1", "2", "5"),
    ),
    "FCW": _series(
        "宽端子厚膜贴片电阻",
        "宽端子 | 无卤",
        {
            size: {"power": power, "voltage": WIDE_VOLTAGE[size], "min_ohm": 0.01, "max_ohm": 10_000_000.0}
            for size, power in WIDE_POWER.items()
        },
        "FCW系列宽电极厚膜片式电阻.pdf",
        tolerances=("1", "5"),
        model_size_by_size={"0612": "1206", "1020": "2010", "1225": "2512"},
    ),
    "FPW": _series(
        "高功率宽端子厚膜贴片电阻",
        "高功率 | 宽端子 | 无卤",
        {
            size: {"power": power, "voltage": WIDE_VOLTAGE[size], "min_ohm": 0.01, "max_ohm": 10_000_000.0}
            for size, power in WIDE_HIGH_POWER.items()
        },
        "FPW系列高功率宽电极厚膜片式电阻.pdf",
        tolerances=("1", "5"),
        model_size_by_size={"0612": "1206", "1020": "2010", "1225": "2512"},
    ),
}


def get_fojan_special_resistor_series():
    return deepcopy(FOJAN_SPECIAL_RESISTOR_SERIES)
