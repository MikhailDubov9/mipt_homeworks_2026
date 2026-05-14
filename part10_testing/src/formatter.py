import math


# NEGATIVE_SIZE_ERROR = "Size cannot be negative"


class FileFormatter:
    def format_file_size(self, size_bytes: int):
        if size_bytes < 0:
            error_message = f"Size cannot be negative: {size_bytes}"
            raise ValueError(error_message)
        if size_bytes == 0:
            return "0B"
        size_name = ["B", "KB", "MB", "GB", "TB"]
        i = math.floor(math.log(size_bytes) / math.log(1024))
        p = math.pow(1024, i)
        s = "{:.2f}".format(size_bytes / p)
        return f"{s} {size_name[i]}"
