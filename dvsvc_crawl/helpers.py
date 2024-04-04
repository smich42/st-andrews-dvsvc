import typing
import tld


def get_fld(url: str) -> str:
    tld_obj = tld.get_tld(url, as_object=True)
    if tld_obj:
        return typing.cast(tld.Result, tld_obj).fld
    raise ValueError(f"Could not extract FLD from URL: {url}")
