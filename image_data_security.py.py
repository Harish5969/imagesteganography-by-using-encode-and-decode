import streamlit as st
from PIL import Image
import numpy as np
import os
import subprocess
import socket

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        return sock.connect_ex(('localhost', port)) == 0

def launch_streamlit_app():
    if not is_port_in_use(8501):
        subprocess.Popen(["streamlit", "run", __file__])

def message_to_binary(message):
    return ''.join(format(byte, '08b') for byte in message.encode('utf-8'))

def binary_to_message(binary):
    try:
        byte_array = bytearray(int(binary[i:i+8], 2) for i in range(0, len(binary), 8) if len(binary[i:i+8]) == 8)
        return byte_array.decode('utf-8')
    except (ValueError, UnicodeDecodeError):
        return "Error in decoding binary message. Check encoding."

def encode_message_LSB(image_path, message):
    img = Image.open(image_path)
    pixels = np.array(img)
    binary_message = message_to_binary(message) + '1111111111111110'  

    data = pixels.reshape(-1)
    for idx, bit in enumerate(binary_message):
        data[idx] = (data[idx] & ~1) | int(bit)

    encoded_pixels = data.reshape(pixels.shape)
    encoded_img = Image.fromarray(encoded_pixels)
    encoded_image_path = "encoded_image_LSB.png"
    encoded_img.save(encoded_image_path)
    return encoded_image_path

def encode_message_LSB_first_two(image_path, message):
    img = Image.open(image_path)
    pixels = np.array(img)
    binary_message = message_to_binary(message) + '1111111111111110' 

    data = pixels.reshape(-1)
    for idx in range(0, len(binary_message), 2):
        bits = binary_message[idx:idx+2]
        if len(bits) < 2:
            bits = bits.ljust(2, '0')
        data_idx = idx // 2
        data[data_idx] = (data[data_idx] & ~3) | int(bits, 2)

    encoded_pixels = data.reshape(pixels.shape)
    encoded_img = Image.fromarray(encoded_pixels)
    encoded_image_path = "encoded_image_LSB_first_two.png"
    encoded_img.save(encoded_image_path)
    return encoded_image_path

def encode_message_F5(image_path, message):
    img = Image.open(image_path)
    pixels = np.array(img)
    binary_message = message_to_binary(message) + '1111111111111110'  

    data = pixels.flatten()
    skip_factor = 5  
    
    for idx, bit in enumerate(binary_message):
        pixel_idx = idx * skip_factor
        if pixel_idx < len(data):
            data[pixel_idx] = (data[pixel_idx] & ~1) | int(bit)

    encoded_pixels = data.reshape(pixels.shape)
    encoded_img = Image.fromarray(encoded_pixels)
    encoded_image_path = "encoded_image_F5.png"
    encoded_img.save(encoded_image_path)
    return encoded_image_path

def decode_message_LSB(image_path):
    img = Image.open(image_path)
    pixels = np.array(img)
    data = pixels.flatten() & 1  
    binary_message = ''.join(map(str, data.tolist()))
    delimiter_index = binary_message.find('1111111111111110')
    if delimiter_index == -1:
        raise ValueError("No valid message found or message delimiter missing.")
    binary_message = binary_message[:delimiter_index]
    return binary_to_message(binary_message)

def decode_message_LSB_first_two(image_path):
    img = Image.open(image_path)
    pixels = np.array(img)
    data = pixels.flatten() & 3 
    binary_message = ''.join(format(byte, '02b') for byte in data.tolist())
    delimiter_index = binary_message.find('1111111111111110')
    if delimiter_index == -1:
        raise ValueError("No valid message found or message delimiter missing.")
    binary_message = binary_message[:delimiter_index]
    return binary_to_message(binary_message)

def decode_message_F5(image_path):
    img = Image.open(image_path)
    pixels = np.array(img)
    data = pixels.flatten() & 1 
    
    skip_factor = 5 
    binary_message = ''.join(map(str, data[::skip_factor]))  
    delimiter_index = binary_message.find('1111111111111110')
    if delimiter_index == -1:
        raise ValueError("No valid message found or message delimiter missing.")
    binary_message = binary_message[:delimiter_index]
    return binary_to_message(binary_message)

def run_streamlit_app():
    st.title("Leveraging Image Data Security Using Steganography Technique")
    col1, col2 = st.columns(2)
    with col1:
        st.header("Encode Message")
        encode_image_file = st.file_uploader("Upload an image to encode the message", type=["jpg", "jpeg", "png", "bmp"])
        message_to_encode = st.text_area("Enter the message you want to encode")

        algorithm_options = ["LSB", "LSB First Two", "F5"]
        algorithm = st.selectbox("Select Encoding Algorithm", algorithm_options)

        if st.button("Encode"):
            if encode_image_file and message_to_encode:
                image_path = f"temp_{encode_image_file.name}"
                with open(image_path, "wb") as f:
                    f.write(encode_image_file.getbuffer())
                
                try:
                    if algorithm == "LSB":
                        encoded_image_path = encode_message_LSB(image_path, message_to_encode)
                    elif algorithm == "LSB First Two":
                        encoded_image_path = encode_message_LSB_first_two(image_path, message_to_encode)
                    elif algorithm == "F5":
                        encoded_image_path = encode_message_F5(image_path, message_to_encode)
                    
                    st.success("Message encoded successfully!")
                    st.image(encoded_image_path, caption="Encoded Image", use_column_width=True)
                    os.remove(image_path)  

                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.error("Please upload an image and enter a message.")
    with col2:
        st.header("Decode Message")
        decode_image_file = st.file_uploader("Upload an image to decode the message", type=["jpg", "jpeg", "png", "bmp"], key="decode")
        algorithm = st.selectbox("Select Decoding Algorithm", algorithm_options, key="decode_algo")

        if st.button("Decode"):
            if decode_image_file:
                image_path = f"temp_{decode_image_file.name}"
                with open(image_path, "wb") as f:
                    f.write(decode_image_file.getbuffer())
                
                try:
                    if algorithm == "LSB":
                        decoded_message = decode_message_LSB(image_path)
                    elif algorithm == "LSB First Two":
                        decoded_message = decode_message_LSB_first_two(image_path)
                    elif algorithm == "F5":
                        decoded_message = decode_message_F5(image_path)
                    
                    st.success("Message decoded successfully!")
                    st.text_area("Decoded Message", decoded_message)
                    os.remove(image_path) 

                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.error("Please upload an image to decode.")

if __name__ == '__main__':
    launch_streamlit_app()
    run_streamlit_app()
