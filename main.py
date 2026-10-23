from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import swisseph as swe
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Authentic Astrological Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)

class BirthDetails(BaseModel):
    year: int
    month: int
    day: int
    hour: int
    minute: int
    timezone_offset: float
    latitude: float
    longitude: float

ZODIAC_SIGNS = [
    "حمل (Aries)", "ثور (Taurus)", "جوزا (Gemini)", 
    "سرطان (Cancer)", "اسد (Leo)", "سنبلہ (Virgo)", 
    "میزان (Libra)", "عقرب (Scorpio)", "قوس (Sagittarius)", 
    "جدی (Capricorn)", "دلو (Aquarius)", "حوت (Pisces)"
]

RULES_MATRIX = {
    (7, "Mars"): {
        "condition": "منگل دوش (Khana 7)",
        "impact": "شادی اور منگنی میں تاخیر، رشتوں میں رکاوٹ اور مزاج میں تیزی۔",
        "remedy": "منگل کے دن سرخ مسور کی دال کا صدقہ دیں اور غصے پر قابو رکھیں۔"
    },
    (5, "Rahu"): {
        "condition": "راہو کی پانچویں خانے میں موجودگی",
        "impact": "اولاد کے حصول میں تاخیر یا تعلیم میں توجہ کی کمی۔",
        "remedy": "بدھ کے دن پرندوں کو دانہ ڈالیں اور چاندی کی کوئی چیز اپنے پاس رکھیں۔"
    }
}

@app.post("/generate_kundli")
def generate_kundli(details: BirthDetails):
    try:
        utc_hour = details.hour + (details.minute / 60.0) - details.timezone_offset
        julian_day = swe.julday(details.year, details.month, details.day, utc_hour)

        flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED

        houses_data, ascmc = swe.houses_ex(julian_day, details.latitude, details.longitude, b'H', flags)
        ascendant_deg = ascmc[0]
        ascendant_sign_idx = int(ascendant_deg // 30)

        planets_to_calc = {
            "Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS, 
            "Mercury": swe.MERCURY, "Jupiter": swe.JUPITER, 
            "Venus": swe.VENUS, "Saturn": swe.SATURN, "Rahu": swe.MEAN_NODE
        }

        calculated_planets = {}

        for p_name, p_code in planets_to_calc.items():
            calc_res, _ = swe.calc_ut(julian_day, p_code, flags)
            longitude = calc_res[0]
            sign_idx = int(longitude // 30)
            sign_deg = round(longitude % 30, 2)

            house_num = ((sign_idx - ascendant_sign_idx) % 12) + 1
            rule_info = RULES_MATRIX.get((house_num, p_name), None)

            calculated_planets[p_name] = {
                "sign": ZODIAC_SIGNS[sign_idx],
                "degree": sign_deg,
                "house": house_num,
                "impact_details": rule_info
            }

        return {
            "status": "success",
            "ascendant": ZODIAC_SIGNS[ascendant_sign_idx],
            "planets": calculated_planets
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
