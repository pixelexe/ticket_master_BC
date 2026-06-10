import httpx

from app.infrastructure.pinata import PinataTicketMetadataStorage


def test_pin_ticket_metadata_uploads_image_then_json(monkeypatch) -> None:
    requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path.endswith("pinFileToIPFS"):
            return httpx.Response(200, json={"IpfsHash": "image-cid"})
        return httpx.Response(200, json={"IpfsHash": "metadata-cid"})

    transport = httpx.MockTransport(handler)
    real_client = httpx.Client
    monkeypatch.setattr(
        httpx,
        "Client",
        lambda **kwargs: real_client(transport=transport, **kwargs),
    )

    storage = PinataTicketMetadataStorage("test-jwt")
    result = storage.pin_ticket_metadata(
        title="VIP",
        description="VIP entrance",
        image_filename="vip.png",
        image_content=b"image",
        image_content_type="image/png",
    )

    assert result == ("ipfs://image-cid", "ipfs://metadata-cid")
    assert len(requests) == 2
    assert requests[0].headers["authorization"] == "Bearer test-jwt"
    assert b'filename="vip.png"' in requests[0].content
    assert b'"image":"ipfs://image-cid"' in requests[1].content
