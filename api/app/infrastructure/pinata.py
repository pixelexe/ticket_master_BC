import json

import httpx

from app.domain.events import MetadataStorageError


class PinataTicketMetadataStorage:
    FILE_URL = "https://api.pinata.cloud/pinning/pinFileToIPFS"
    JSON_URL = "https://api.pinata.cloud/pinning/pinJSONToIPFS"

    def __init__(self, jwt: str):
        self.jwt = jwt

    def pin_ticket_metadata(
        self,
        title: str,
        description: str,
        image_filename: str,
        image_content: bytes,
        image_content_type: str,
    ) -> tuple[str, str]:
        if not self.jwt:
            raise MetadataStorageError("PINATA_JWT is not configured")

        headers = {"Authorization": f"Bearer {self.jwt}"}

        try:
            with httpx.Client(timeout=60) as client:
                image_response = client.post(
                    self.FILE_URL,
                    headers=headers,
                    files={
                        "file": (
                            image_filename,
                            image_content,
                            image_content_type,
                        )
                    },
                    data={
                        "pinataMetadata": json.dumps(
                            {"name": image_filename}
                        ),
                        "pinataOptions": json.dumps({"cidVersion": 1}),
                    },
                )
                image_response.raise_for_status()
                image_uri = f"ipfs://{image_response.json()['IpfsHash']}"

                metadata_response = client.post(
                    self.JSON_URL,
                    headers=headers,
                    json={
                        "pinataOptions": {"cidVersion": 1},
                        "pinataMetadata": {
                            "name": f"{title}-metadata.json"
                        },
                        "pinataContent": {
                            "name": title,
                            "description": description,
                            "image": image_uri,
                        },
                    },
                )
                metadata_response.raise_for_status()
                metadata_uri = (
                    f"ipfs://{metadata_response.json()['IpfsHash']}"
                )
        except (httpx.HTTPError, KeyError) as error:
            raise MetadataStorageError("Pinata upload failed") from error

        return image_uri, metadata_uri
