from django.core.mail import send_mail
from django.conf import settings
from dropbox_sign import ApiClient, ApiException, Configuration, apis
import cloudinary.uploader
import os
import tempfile
import cloudinary
import time


def download_and_upload_signed_contract(signature_request_id):
    configuration = Configuration(
        username="c35b8f89b102910d72f6c05bf78097f62e8e9e2f28c164a587ba0ab331bca22d"
    )

    temp_file_path = None
    max_retries = 8
    retry_interval = 5  # Delay between retries in seconds

    with ApiClient(configuration) as api_client:
        signature_request_api = apis.SignatureRequestApi(api_client)

        for retry_count in range(max_retries):
            try:
                print("Attempting to download file...")
                response = signature_request_api.signature_request_files(
                    signature_request_id, file_type="pdf"
                )
                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=".pdf"
                ) as temp_file:
                    temp_file.write(response.read())
                    temp_file_path = temp_file.name
                print("File downloaded successfully.")
                break  # Exit the loop if file download is successful
            except ApiException as e:
                print("Exception when calling Dropbox Sign API: %s\n" % e)

            if retry_count < max_retries - 1:
                print(
                    f"Retry #{retry_count + 1} - Waiting {retry_interval} seconds before retrying..."
                )
                time.sleep(retry_interval)

        # Upload the signed contract to Cloudinary and get the URL
        if temp_file_path:
            try:
                print("Attempting to upload file...")
                print("Temp file path:", temp_file_path)

                with open(temp_file_path, "rb") as file_to_upload:  # Open the file
                    upload_response = cloudinary.uploader.upload(
                        file_to_upload, resource_type="auto"  # Upload the file
                    )
                cloudinary_url = upload_response["secure_url"]
                print("File uploaded successfully. URL:", cloudinary_url)
            except cloudinary.exceptions.Error as e:
                print("Exception when calling Cloudinary API: %s\n" % e)
                return None

            # Remove the temporary file after use
            os.remove(temp_file_path)

            return cloudinary_url

    return None
