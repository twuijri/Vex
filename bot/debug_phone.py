
import re
import unicodedata

def check_phone(raw_text):
    print(f"\n--- Testing: {raw_text} ---")
    
    # 1. Cleaner
    clean_content = ''.join(c for c in unicodedata.normalize('NFD', raw_text)
                   if unicodedata.category(c) != 'Mn')
    print(f"Cleaned: {clean_content}")
    
    # 2. Phone Logic
    phone_clean_text = re.sub(r'[\s\-]', '', clean_content)
    print(f"Phone Ready: {phone_clean_text}")
    
    phone_pattern = r'(\+|00|0|٠٠|٠)[\d٠-٩]{8,}'
    
    match = re.search(phone_pattern, phone_clean_text)
    if match:
        print(f"✅ MATCH FOUND: {match.group()}")
    else:
        print(f"❌ NO MATCH")

# Test Cases
check_phone("٠٥٥٥٥٥٥٢١٠")
check_phone("0555555210")
check_phone("+966542852718")
check_phone("و̶ت̶ساب +966 54 285 2718")
check_phone("للتواصل ٠٥٥-٥٥٥-٥٢١٠")
