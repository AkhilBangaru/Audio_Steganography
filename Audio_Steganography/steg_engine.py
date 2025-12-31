import wave
import struct
import zlib
import base64
import os
import io
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class StegEngine:
    OFFSET_BYTES = 1000  # Offset to avoid header corruption, though wave module handles frames directly.
    # We will simply write frames. But actually, using the wave module we deal with raw frames.
    # Safe to start from 0 if we use wave module properly.

    @staticmethod
    def derive_key(password: str, salt: bytes) -> bytes:
        """Derives a 32-byte key from the password using PBKDF2HMAC."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100_000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))

    @staticmethod
    def encrypt_data(data: bytes, password: str) -> bytes:
        """Compresses and encrypts data. Returns Salt + Encrypted Data."""
        # 1. Compress
        compressed = zlib.compress(data)
        
        # 2. Derive Key
        salt = os.urandom(16)
        key = StegEngine.derive_key(password, salt)
        f = Fernet(key)
        
        # 3. Encrypt
        encrypted = f.encrypt(compressed)
        
        # Return Salt + Encrypted Data
        return salt + encrypted

    @staticmethod
    def decrypt_data(data: bytes, password: str) -> bytes:
        """Decrypts and extracts data. Expects Salt + Encrypted Data."""
        try:
            salt = data[:16]
            encrypted = data[16:]
            
            key = StegEngine.derive_key(password, salt)
            f = Fernet(key)
            
            decrypted_compressed = f.decrypt(encrypted)
            return zlib.decompress(decrypted_compressed)
        except Exception as e:
            raise ValueError(f"Decryption failed: {str(e)}")

    def embed(self, audio_data: bytes, params, secret_payload: bytes, password: str) -> bytes:
        """
        Embeds secret payload into audio data.
        Params: wave params (nchannels, sampwidth, framerate, nframes, comptype, compname)
        """
        # Prepare payload
        encrypted_blob = self.encrypt_data(secret_payload, password)
        payload_len = len(encrypted_blob)
        
        # Protocol: [4-byte Length] + [Encrypted Blob]
        final_payload = struct.pack('>I', payload_len) + encrypted_blob
        
        # Check capacity
        # We need 8 bits (samples) per byte of data for LSB
        frame_bytes = bytearray(audio_data)
        required_samples = len(final_payload) * 8
        
        if len(frame_bytes) < required_samples:
             raise ValueError(f"Audio file too small. Need {required_samples} samples, got {len(frame_bytes)}.")

        # LSB Injection
        # We iterate through the payload bits and modify the LSB of each byte in audio data
        data_index = 0
        payload_bits = []
        
        # Convert payload to list of bits
        for byte in final_payload:
            for i in range(7, -1, -1):
                payload_bits.append((byte >> i) & 1)

        # Inject bits
        for i, bit in enumerate(payload_bits):
            # Clear LSB and set it to bit
            frame_bytes[i] = (frame_bytes[i] & 0xFE) | bit
            
        return bytes(frame_bytes)

    def extract(self, audio_data: bytes, password: str) -> tuple[str, str, bytes]:
        """
        Extracts execution payload.
        Returns: (Type, Filename, Data)
        """
        frame_bytes = bytearray(audio_data)
        
        # 1. Read Length (First 32 bits -> 4 bytes)
        length_bits = []
        for i in range(32):
             length_bits.append(frame_bytes[i] & 1)
        
        length_val = 0
        for bit in length_bits:
            length_val = (length_val << 1) | bit
            
        # 2. Read Encrypted Blob
        # Start reading from index 32
        payload_bits = []
        total_bits = length_val * 8
        
        # Check bounds
        if 32 + total_bits > len(frame_bytes):
             raise ValueError("Detected data length exceeds file size. File might be corrupted or not encoded.")
        
        for i in range(32, 32 + total_bits):
            payload_bits.append(frame_bytes[i] & 1)
            
        # Reconstruct bytes
        encrypted_data_array = bytearray()
        for i in range(0, len(payload_bits), 8):
            byte_val = 0
            for j in range(8):
                byte_val = (byte_val << 1) | payload_bits[i+j]
            encrypted_data_array.append(byte_val)
            
        encrypted_data = bytes(encrypted_data_array)
        
        # 3. Decrypt & Decompress
        decrypted_payload = self.decrypt_data(encrypted_data, password)
        
        # 4. Parse Protocol: "TYPE|||FILENAME|||DATA"
        # We use a custom separator that is unlikely to appear in headers, 
        # but the content itself is binary.
        # Actually, if the DATA is binary, we can't use string split easily on the whole thing.
        # We should probably define the protocol better or handle binary carefully.
        # Let's assume the separator is bytes: b'|||'
        
        parts = decrypted_payload.split(b'|||', 2)
        if len(parts) < 3:
            raise ValueError("Invalid payload format.")
            
        msg_type = parts[0].decode('utf-8')
        filename = parts[1].decode('utf-8')
        actual_data = parts[2]
        
        return msg_type, filename, actual_data

