class Log:
    enabled_zones = set()
    enabled_zones_stripped = set()

    @staticmethod
    def print(s):
        if ':' in s:
            zone = s.split(':')[0]
        else:
            zone = None

        if zone is None or zone in Log.enabled_zones:
            if zone in Log.enabled_zones_stripped:
                s = s[len(zone) + 1:].lstrip(' ')
                print(s)
            else:
                print('* %s' % s)

    def enable(zone, stripped=False):
        Log.enabled_zones.add(zone)
        if stripped:
            Log.enabled_zones_stripped.add(zone)

    def disable(zone):
        Log.enabled_zones.remove(zone)
        if zone in Log.enabled_zones_stripped:
            Log.enabled_zones_stripped.remove(zone)
