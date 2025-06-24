from pynput.keyboard import Controller, Key
import time

# 初始化鍵盤控制器
keyboard = Controller()

def press_and_release_key(key_char_or_special_key):
    """
    模擬按下並釋放指定的按鍵。
    :param key_char_or_special_key: 可以是單個字符 (e.g., 'a'),
                                   或者是 pynput.keyboard.Key 中的特殊按鍵 (e.g., Key.space, Key.enter).
    """
    try:
        if isinstance(key_char_or_special_key, str) and len(key_char_or_special_key) == 1:
            # 如果是單個字符
            print(f"模擬按下按鍵: {key_char_or_special_key}")
            keyboard.press(key_char_or_special_key)
            time.sleep(0.05) # 短暫延遲以確保按鍵被系統識別
            keyboard.release(key_char_or_special_key)
            print(f"模擬釋放按鍵: {key_char_or_special_key}")
        elif isinstance(key_char_or_special_key, Key):
            # 如果是特殊按鍵
            print(f"模擬按下特殊按鍵: {key_char_or_special_key}")
            keyboard.press(key_char_or_special_key)
            time.sleep(0.05)
            keyboard.release(key_char_or_special_key)
            print(f"模擬釋放特殊按鍵: {key_char_or_special_key}")
        else:
            print(f"錯誤: 不支援的按鍵類型 '{key_char_or_special_key}'")
            return False
        return True
    except Exception as e:
        print(f"模擬按鍵時發生錯誤: {e}")
        # 在macOS上，可能需要輔助功能權限
        # "This process is not trusted! See https://pynput.readthedocs.io/en/latest/troubleshooting.html#macos"
        if "rocess is not trusted" in str(e):
            print("--------------------------------------------------------------------")
            print("macOS 權限問題：請確保您的終端或IDE具有輔助使用權限。")
            print("前往 系統設定 > 隱私權與安全性 > 輔助使用，然後將您的應用程式加入列表。")
            print("如果從終端運行，請將終端應用程式加入。")
            print("--------------------------------------------------------------------")
        return False

if __name__ == '__main__':
    # 測試
    print("將在3秒後模擬按下 'h' 鍵...")
    time.sleep(3)
    press_and_release_key('h')
    time.sleep(1)

    print("將在2秒後模擬按下 'e' 鍵...")
    time.sleep(2)
    press_and_release_key('e')
    time.sleep(1)

    print("將在2秒後模擬按下 空白鍵...")
    time.sleep(2)
    press_and_release_key(Key.space)
    time.sleep(1)

    print("將在2秒後模擬按下 Enter 鍵...")
    time.sleep(2)
    press_and_release_key(Key.enter)
    print("測試完成。")
