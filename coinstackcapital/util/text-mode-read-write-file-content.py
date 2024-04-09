def copy_file_content(input_file_path, output_file_path):
    try:
        with open(input_file_path, 'r') as input_file: #, open(output_file_path, 'w') as output_file:
            # Read content from the input file
            file_content = input_file.read()
            
            # Write the content to the output file
            #output_file.write(file_content)

            return file_content
    except Exception as e:
        # Handle any exceptions (e.g., file not found, permission issues)
        return f"Error: {str(e)}"


# Example usage
input_path = '../email_templates/verify_email.html'  # Replace with the actual input file path
output_path = 'output.txt'  # Replace with the desired output file path

copied_content = copy_file_content(input_path, output_path)

if 'Error' not in copied_content:
    print("File content copied successfully.")
    print("Copied Content:")
    print(copied_content)
else:
    print(f"Error occurred: {copied_content}")

if __name__ == "__main__":
    print(copy_file_content(input_path,output_path))
    pass