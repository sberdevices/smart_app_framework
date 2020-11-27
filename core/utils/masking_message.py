

MASK = "***"
DEFAULT_MASKING_FIELDS = ["token", "access_token", "refresh_token", "epkId", "profileId"]


def masking(data, masking_fields=None):
    if masking_fields is None:
        masking_fields = DEFAULT_MASKING_FIELDS
    if hasattr(data, 'items'):
        for key in data:
            if key in masking_fields:
                data[key] = MASK
            elif isinstance(data[key], dict):
                masking(data[key], masking_fields)
            elif isinstance(data[key], list):
                for item in data[key]:
                    masking(item, masking_fields)
