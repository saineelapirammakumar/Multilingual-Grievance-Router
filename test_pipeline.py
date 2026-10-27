from app.language_id import detect_language
from app.translation import translate_to_english
from app.urgency import apply_safety
def test_tamil():assert detect_language("தண்ணீர் வரவில்லை")["language"]=="Tamil"
def test_hindi():assert detect_language("पानी नहीं आ रहा")["language"]=="Hindi"
def test_tanglish():assert "Tanglish" in detect_language("street la water varala")["language"]
def test_emergency():assert apply_safety("live wire near school","Routine")[0]=="Emergency"
def test_translation():assert "water" in translate_to_english("paani nahi aa raha","Hinglish")[0]
