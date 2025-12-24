
import unicodedata
import re

def clean_text(text):
    print(f"\n--- Original: {text} ---")
    
    # 1. Normalize NFD (Decompose)
    nfd_text = unicodedata.normalize('NFD', text)
    
    # 2. Filter Mn (Mark, Nonspacing) - Diacritics
    no_marks = ''.join(c for c in nfd_text if unicodedata.category(c) != 'Mn')
    
    # 3. Tatweel Removal (ـ)
    no_tatweel = no_marks.replace("ـ", "")
    
    # Recompose
    final = unicodedata.normalize('NFC', no_tatweel)
    
    print(f"Cleaned:  {final}")
    return final

spam_msg = """ـنطٌٰٰـِٰعّْ 'عٌذأّر -طِبًيِّةّ- صّـحًتٌـيِّ' مًعٌتٌـمًدٍةّ 
    ♡•••/لَجّمًيَعٌ آلَقُطِآعٌآتٌ/•••♡
 كُـٰوٌِيِّسٌِْـٰـّةّ إذٌآ تٌـٰبًوٌُنًُْٓ"""

cleaned = clean_text(spam_msg)

# Check for keywords the user might want to ban
keywords = ["طبي", "طبية", "عذر", "صحتي", "معتمدة", "اجازات", "كويس"]
print("\n--- Keyword Check ---")
for k in keywords:
    if k in cleaned:
        print(f"✅ Found banned word candidate: {k}")
    else:
        pass
