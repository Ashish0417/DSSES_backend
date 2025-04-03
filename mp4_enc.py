from Crypto.Cipher import DES
from Crypto.Util.Padding import pad, unpad
import os

def des_encrypt_file(input_file, output_file, key):
    cipher = DES.new(key, DES.MODE_ECB)
    
    with open(input_file, 'rb') as f:
        data = f.read()
    
    padded_data = pad(data, DES.block_size)
    encrypted_data = cipher.encrypt(padded_data)
    
    with open(output_file, 'wb') as f:
        f.write(encrypted_data)

    print(f"Encrypted file saved as: {output_file}")

# # Example usage
# key = b'abcdefgh'  # 8-byte key (Ensure it's securely generated)
# des_encrypt_file("input.mp4", "encrypted.mp4", key)

def des_decrypt_file(input_file, output_file, key):
    cipher = DES.new(key, DES.MODE_ECB)

    with open(input_file, 'rb') as f:
        encrypted_data = f.read()

    decrypted_padded_data = cipher.decrypt(encrypted_data)
    decrypted_data = unpad(decrypted_padded_data, DES.block_size)

    with open(output_file, 'wb') as f:
        f.write(decrypted_data)

    print(f"Decrypted file saved as: {output_file}")

# Example usage
# des_decrypt_file("encrypted.mp4", "decrypted.mp4", key)
