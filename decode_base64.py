#!/usr/bin/env python3
"""
Simple utility to decode base64 data from webhook payloads
"""

import base64
import json
import sys

def decode_base64_string(b64_string):
    """Decode a base64 string and try to parse as JSON"""
    try:
        # Remove any whitespace
        b64_string = b64_string.strip()
        
        # Decode base64
        decoded_bytes = base64.b64decode(b64_string)
        decoded_string = decoded_bytes.decode('utf-8')
        
        print("✅ Base64 decoded successfully!")
        print(f"📝 Raw decoded string length: {len(decoded_string)} characters")
        print()
        
        # Try to parse as JSON
        try:
            decoded_json = json.loads(decoded_string)
            print("✅ Successfully parsed as JSON!")
            print("📊 Formatted JSON:")
            print(json.dumps(decoded_json, indent=2))
            return decoded_json, decoded_string
        except json.JSONDecodeError as e:
            print("⚠️ Not valid JSON, showing raw text:")
            print(decoded_string)
            return None, decoded_string
            
    except Exception as e:
        print(f"❌ Error decoding base64: {str(e)}")
        return None, None

def main():
    """Main function for interactive or command-line usage"""
    print("🔧 Base64 Decoder Utility")
    print("=" * 40)
    
    if len(sys.argv) > 1:
        # Command line usage
        b64_string = sys.argv[1]
        print(f"Decoding provided base64 string...")
        decode_base64_string(b64_string)
    else:
        # Interactive usage
        print("Enter a base64 string to decode (or 'quit' to exit):")
        
        while True:
            try:
                user_input = input("\n> ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                    
                if not user_input:
                    print("Please enter a base64 string.")
                    continue
                    
                print(f"\n🔍 Decoding: {user_input[:50]}{'...' if len(user_input) > 50 else ''}")
                print("-" * 40)
                
                decode_base64_string(user_input)
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except EOFError:
                print("\n👋 Goodbye!")
                break

if __name__ == "__main__":
    main()
