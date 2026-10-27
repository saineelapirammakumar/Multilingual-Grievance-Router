TAMIL={"தண்ணீர்":"water","வரவில்லை":"not coming","குழாய்":"pipe","உடைந்து":"broken","சாலை":"road","குப்பை":"garbage","மூன்று":"three","நாட்களாக":"days","எடுக்கவில்லை":"not collected","முழுவதும்":"completely","பள்ளங்கள்":"potholes","மின்கம்பம்":"electric pole","விழுந்து":"fallen","மறித்துள்ளது":"blocking","பள்ளி":"school","அருகே":"near","மின்கம்பி":"electric wire","அறுந்து":"broken","தெருவிளக்கு":"street light","வேலை":"work","செய்யவில்லை":"not working","சாக்கடை":"drain","நீர்":"water","சாலையில்":"on road","பெருக்கெடுத்து":"overflowing","ஓடுகிறது":"running","கழிவுநீர்":"sewage","வீட்டுக்குள்":"inside house","குடிநீர்":"drinking water","அழுக்காக":"dirty","தொட்டி":"bin","நிரம்பி":"full","வழிகிறது":"overflowing","கசிகிறது":"leaking"}
HINDI={"पानी":"water","नहीं":"not","आ":"coming","रहा":"is","गली":"street","कचरा":"garbage","बिजली":"electricity","तार":"wire","सड़क":"road","नाली":"drain","गंदा":"dirty","गिर":"fell","गया":"down","है":"is","बहुत":"very","पास":"near","स्कूल":"school"}
ROMAN={"thanni":"water","tanni":"water","thanneer":"water","varala":"not coming","paani":"water","pani":"water","nahi":"not","gali":"street","kachra":"garbage","bijli":"electricity","taar":"wire","sadak":"road","ganda":"dirty","pakkathula":"near","kuzhai":"pipe","kuppai":"garbage","naali":"drain","sakkadai":"sewage","mela":"on","vizhundhuduchu":"fell down","vizhundhu":"fell","irukku":"there is","aagala":"not working","aagudhu":"is happening","pannala":"not done","romba naala":"for many days"}

ROMAN.update({'pakkam':'near','aaguthu':'happening','varalai':'not coming','kharab':'broken','latak':'hanging','neeche':'low','gir gaya':'fallen','aa raha':'coming','romba naala':'many days','odudhu':'flowing','innaiku':'today','night':'night','romba':'very','dark':'dark','safe':'safe','safely':'safely','poga':'go','mudiyala':'cannot','accident':'accident','nadanthirukku':'happened','injured':'injured','help':'help','venum':'needed','ippo':'now','people':'people','road':'road'})
TAMIL.update({'விழுந்துள்ளது':'fallen','மின்சாரம்':'electricity','பள்ளங்கள்':'potholes','மின்விளக்கு':'street light','வருகிறது':'coming'})
HINDI.update({'खराब':'broken','लीक':'leak','टूटी':'broken','गड्ढे':'potholes'})
import re, unicodedata

def tr(text, mapping):
    # Match whole Unicode tokens, including phrase boundaries; never alter 'paint' via 'pani'.
    pattern=r'(?<!\w)('+'|'.join(re.escape(k) for k in sorted(mapping,key=len,reverse=True))+r')(?!\w)'
    return re.sub(pattern,lambda m:' '+mapping[m.group(0)]+' ',text)

def normalize(text):
    text=unicodedata.normalize('NFKC',text).lower()
    text=re.sub(r'[\u200b-\u200d\ufeff]','',text)
    # Original script stays in feature input; mapped civic concepts supplement it.
    mapped=text
    for d in (TAMIL,HINDI,ROMAN): mapped=tr(mapped,d)
    mapped=re.sub(r'\b(watr|watter)\b','water',mapped)
    mapped=re.sub(r'\b(leeking|leekingg)\b','leaking',mapped)
    return ' '.join(mapped.split())

def feature_text(text):
    original=' '.join(unicodedata.normalize('NFKC',text).lower().split())
    mapped=normalize(text)
    return original if mapped==original else original+' '+mapped

def translate_to_english(text,language=None):
    return normalize(text),'civic-lexicon-normalization-not-translation'
