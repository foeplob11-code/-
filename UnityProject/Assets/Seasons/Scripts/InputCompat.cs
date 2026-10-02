using UnityEngine;
#if ENABLE_INPUT_SYSTEM
using UnityEngine.InputSystem;
#endif

namespace RealisticSeasons
{
    /// <summary>
    /// Minimal input wrapper so the demo runs with either the legacy Input Manager
    /// or the Input System package (whichever the project has enabled).
    /// </summary>
    public static class InputCompat
    {
        public enum Button { Left, Right, Middle }

#if ENABLE_INPUT_SYSTEM
        static readonly Key[] Digits = { Key.Digit0, Key.Digit1, Key.Digit2, Key.Digit3, Key.Digit4 };
        static readonly Key[] Numpad = { Key.Numpad0, Key.Numpad1, Key.Numpad2, Key.Numpad3, Key.Numpad4 };
#endif

        /// <summary>Number key 0-4 (top row or numpad) pressed this frame.</summary>
        public static bool DigitDown(int digit)
        {
#if ENABLE_INPUT_SYSTEM
            var kb = Keyboard.current;
            return kb != null && (kb[Digits[digit]].wasPressedThisFrame || kb[Numpad[digit]].wasPressedThisFrame);
#else
            return Input.GetKeyDown(KeyCode.Alpha0 + digit) || Input.GetKeyDown(KeyCode.Keypad0 + digit);
#endif
        }

        /// <summary>Letter key A-Z pressed this frame.</summary>
        public static bool LetterDown(char letter)
        {
            int i = char.ToUpperInvariant(letter) - 'A';
#if ENABLE_INPUT_SYSTEM
            var kb = Keyboard.current;
            return kb != null && kb[(Key)((int)Key.A + i)].wasPressedThisFrame;
#else
            return Input.GetKeyDown((KeyCode)((int)KeyCode.A + i));
#endif
        }

        public static bool ShiftHeld()
        {
#if ENABLE_INPUT_SYSTEM
            var kb = Keyboard.current;
            return kb != null && kb.shiftKey.isPressed;
#else
            return Input.GetKey(KeyCode.LeftShift) || Input.GetKey(KeyCode.RightShift);
#endif
        }

        public static bool Held(Button button)
        {
#if ENABLE_INPUT_SYSTEM
            var m = Mouse.current;
            if (m == null) return false;
            switch (button)
            {
                case Button.Left: return m.leftButton.isPressed;
                case Button.Right: return m.rightButton.isPressed;
                default: return m.middleButton.isPressed;
            }
#else
            return Input.GetMouseButton((int)button);
#endif
        }

        public static Vector2 MousePosition()
        {
#if ENABLE_INPUT_SYSTEM
            var m = Mouse.current;
            return m != null ? m.position.ReadValue() : Vector2.zero;
#else
            return Input.mousePosition;
#endif
        }

        /// <summary>Wheel movement in notches; positive = away from the user.</summary>
        public static float Scroll()
        {
#if ENABLE_INPUT_SYSTEM
            var m = Mouse.current;
            if (m == null) return 0f;
            float y = m.scroll.ReadValue().y;
            return Mathf.Abs(y) >= 10f ? y / 120f : y;   // some platforms report raw ±120 per notch
#else
            return Input.mouseScrollDelta.y;
#endif
        }

        /// <summary>WASD / arrow keys as a -1..1 vector (x = right, y = forward).</summary>
        public static Vector2 Move()
        {
            Vector2 v = Vector2.zero;
#if ENABLE_INPUT_SYSTEM
            var kb = Keyboard.current;
            if (kb == null) return v;
            if (kb.dKey.isPressed || kb.rightArrowKey.isPressed) v.x += 1f;
            if (kb.aKey.isPressed || kb.leftArrowKey.isPressed) v.x -= 1f;
            if (kb.wKey.isPressed || kb.upArrowKey.isPressed) v.y += 1f;
            if (kb.sKey.isPressed || kb.downArrowKey.isPressed) v.y -= 1f;
#else
            if (Input.GetKey(KeyCode.D) || Input.GetKey(KeyCode.RightArrow)) v.x += 1f;
            if (Input.GetKey(KeyCode.A) || Input.GetKey(KeyCode.LeftArrow)) v.x -= 1f;
            if (Input.GetKey(KeyCode.W) || Input.GetKey(KeyCode.UpArrow)) v.y += 1f;
            if (Input.GetKey(KeyCode.S) || Input.GetKey(KeyCode.DownArrow)) v.y -= 1f;
#endif
            return v;
        }
    }
}
