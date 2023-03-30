def GeoIP(path):
    import geoip2.database
    geoip = geoip2.database.Reader(path)

    def ip2name(ip):
        try:
            response = geoip.country(ip)
            return response.country.names["en"]
        except geoip2.errors.GeoIP2Error:
            return "unknown"

    def ip2code(ip):
        try:
            response = geoip.country(ip)
            return response.country.iso_code
        except geoip2.errors.GeoIP2Error:
            return "unknown"

    return ip2name, ip2code
