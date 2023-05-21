from django.core.mail import send_mail
from django.conf import settings
from dropbox_sign import ApiClient, ApiException, Configuration, apis
import cloudinary.uploader
import os
import tempfile
import time
from django.http import HttpResponse


def send_email(recipient_list, subject, message):
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=recipient_list,
        fail_silently=False,
    )


def download_and_upload_signed_contract(
    signature_request_id, retry_attempts=5, delay=5
):
    configuration = Configuration(
        username="c35b8f89b102910d72f6c05bf78097f62e8e9e2f28c164a587ba0ab331bca22d"
    )

    with ApiClient(configuration) as api_client:
        signature_request_api = apis.SignatureRequestApi(api_client)

        for _ in range(retry_attempts):
            try:
                response = signature_request_api.signature_request_files_as_file_url(
                    signature_request_id
                )
                signed_document_url = response.file_url

                if signed_document_url:
                    # Upload URL directly to Cloudinary
                    upload_result = cloudinary.uploader.upload(signed_document_url)
                    return upload_result["secure_url"]

            except ApiException as e:
                print("Exception when calling Dropbox Sign API: %s\n" % e)

            time.sleep(delay)

    return None


def download_signed_file(request, signature_request_id):
    file_type = "pdf"
    print("signature_request_api: ", signature_request_api)
    # Configure the HelloSign/Dropbox Sign API client
    configuration = Configuration(
        username="c35b8f89b102910d72f6c05bf78097f62e8e9e2f28c164a587ba0ab331bca22d",
        # Set other configuration options as needed
    )
    api_client = ApiClient(configuration)
    signature_request_api = apis.SignatureRequestApi(api_client)

    try:
        # Download the signed file using the signature request ID and file type
        response = signature_request_api.signature_request_files(
            signature_request_id, file_type=file_type
        )

        # Create the response with the file contents
        response_file = response.read()
        http_response = HttpResponse(response_file, content_type="application/pdf")
        http_response["Content-Disposition"] = 'attachment; filename="signed_file.pdf"'
        return http_response
    except ApiException as e:
        # Handle API exceptions
        return HttpResponse("Error downloading signed file: {}".format(str(e)))
