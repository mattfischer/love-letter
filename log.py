class Log:
    enabled_zones = set()

    @staticmethod
    def print(s):
        if ':' in s:
            zone = s.split(':')[0]
        else:
            zone = None

        if zone is None or zone in Log.enabled_zones:
            print('* %s' % s)

    def enable(zone):
        Log.enabled_zones.add(zone)

    def disable(zone):
        Log.enabled_zones.remove(zone)
