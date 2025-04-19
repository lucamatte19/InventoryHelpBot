def format_remaining_time(seconds: int) -> str:
    """Formatta i secondi in un stringa mm:ss o hh:mm:ss o dd:hh:mm:ss."""
    if seconds < 0: seconds = 0
    
    days = seconds // 86400
    remaining_seconds = seconds % 86400
    hours = remaining_seconds // 3600
    remaining_seconds %= 3600
    minutes = remaining_seconds // 60
    secs = remaining_seconds % 60
    
    if days > 0:
        return f"{days}g {hours:02d}:{minutes:02d}:{secs:02d}"
    elif hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"

def parse_dhms_time(time_str):
    """Parses dd:hh:mm:ss or hh:mm:ss format and returns total seconds."""
    try:
        parts = list(map(int, time_str.split(':')))
        if len(parts) == 4:  # dd:hh:mm:ss
            d, h, m, s = parts
            if d < 0 or h < 0 or h > 23 or m < 0 or m > 59 or s < 0 or s > 59:
                print(f"Invalid time components: {d}:{h}:{m}:{s}")
                return None  # Invalid time components
            total_seconds = d * 86400 + h * 3600 + m * 60 + s
            print(f"Parsed dd:hh:mm:ss format: {d}:{h}:{m}:{s} = {total_seconds} seconds")
            return total_seconds
        elif len(parts) == 3:  # hh:mm:ss
            h, m, s = parts
            if h < 0 or m < 0 or m > 59 or s < 0 or s > 59:
                print(f"Invalid time components: {h}:{m}:{s}")
                return None  # Invalid time components
            total_seconds = h * 3600 + m * 60 + s
            print(f"Parsed hh:mm:ss format: {h}:{m}:{s} = {total_seconds} seconds")
            return total_seconds
        else:
            print(f"Invalid number of time components: {len(parts)}")
            return None
    except ValueError as e:
        print(f"Error parsing time: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error parsing time: {e}")
        return None
