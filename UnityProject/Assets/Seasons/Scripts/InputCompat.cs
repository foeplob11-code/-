// Use the Input System package only when it is actually installed (SEASONS_INPUT_SYSTEM comes from the
// asmdef's version define) AND enabled in Player Settings; otherwise fall back to the legacy Input Manager.
#if ENABLE_INPUT_SYSTEM && SEASONS_INPUT_SYSTEM
#define SEASONS_NEW_INPUT
#elif ENABLE_LEGACY_INPUT_MANAGER
#define SEASONS_OLD_INPUT
#endif

using UnityEngine;
#if SEASONS_NEW_INPUT
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

#if SEASONS_NEW_INPUT
        static readonly Key[] Digits = { Key.Digit0, Key.Digit1, Key.Digit2, Key.Digit3, Key.Digit4 };
        static readonly Key[] Numpad = { Key.Numpad0, Key.Numpad1, Key.Numpad2, Key.Numpad3, Key.Numpad4 };
#endif

        /// <summary>Number key 0-4 (top row or numpad) pressed this frame.</summary>
        public static bool DigitDown(int digit)
        {
#if SEASONS_NEW_INPUT
            var kb = Keyboard.current;
            return kb != null && (kb[Digits[digit]].wasPressedThisFrame || kb[Numpad[digit]].wasPressedThisFrame);
#elif SEASONS_OLD_INPUT
            return Input.GetKeyDown(KeyCode.Alpha0 + digit) || Input.GetKeyDown(KeyCode.Keypad0 + digit);
#else
            return false;
#endif
        }

        /// <summary>Letter key A-Z pressed this frame.</summary>
        public static bool LetterDown(char letter)
        {
#if SEASONS_NEW_INPUT
            var kb = Keyboard.current;
            return kb != null && kb[(Key)((int)Key.A + char.ToUpperInvariant(letter) - 'A')].wasPressedThisFrame;
#elif SEASONS_OLD_INPUT
            return Input.GetKeyDown((KeyCode)((int)KeyCode.A + char.ToUpperInvariant(letter) - 'A'));
#else
            return false;
#endif
        }

        public static bool EscapeDown()
        {
#if SEASONS_NEW_INPUT
            var kb = Keyboard.current;
            return kb != null && kb.escapeKey.wasPressedThisFrame;
#elif SEASONS_OLD_INPUT
            return Input.GetKeyDown(KeyCode.Escape);
#else
            return false;
#endif
        }

        public static bool ShiftHeld()
        {
#if SEASONS_NEW_INPUT
            var kb = Keyboard.current;
            return kb != null && kb.shiftKey.isPressed;
#elif SEASONS_OLD_INPUT
            return Input.GetKey(KeyCode.LeftShift) || Input.GetKey(KeyCode.RightShift);
#else
            return false;
#endif
        }

        public static bool Held(Button button)
        {
#if SEASONS_NEW_INPUT
            var m = Mouse.current;
            if (m == null) return false;
            switch (button)
            {
                case Button.Left: return m.leftButton.isPressed;
                case Button.Right: return m.rightButton.isPressed;
                default: return m.middleButton.isPressed;
            }
#elif SEASONS_OLD_INPUT
            return Input.GetMouseButton((int)button);
#else
            return false;
#endif
        }

        public static Vector2 MousePosition()
        {
#if SEASONS_NEW_INPUT
            var m = Mouse.current;
            return m != null ? m.position.ReadValue() : Vector2.zero;
#elif SEASONS_OLD_INPUT
            return Input.mousePosition;
#else
            return Vector2.zero;
#endif
        }

        /// <summary>Wheel movement in notches; positive = away from the user.</summary>
        public static float Scroll()
        {
#if SEASONS_NEW_INPUT
            var m = Mouse.current;
            if (m == null) return 0f;
            float y = m.scroll.ReadValue().y;
            return Mathf.Abs(y) >= 10f ? y / 120f : y;   // some platforms report raw ±120 per notch
#elif SEASONS_OLD_INPUT
            return Input.mouseScrollDelta.y;
#else
            return 0f;
#endif
        }

        /// <summary>WASD / arrow keys as a -1..1 vector (x = right, y = forward).</summary>
        public static Vector2 Move()
        {
            Vector2 v = Vector2.zero;
#if SEASONS_NEW_INPUT
            var kb = Keyboard.current;
            if (kb == null) return v;
            if (kb.dKey.isPressed || kb.rightArrowKey.isPressed) v.x += 1f;
            if (kb.aKey.isPressed || kb.leftArrowKey.isPressed) v.x -= 1f;
            if (kb.wKey.isPressed || kb.upArrowKey.isPressed) v.y += 1f;
            if (kb.sKey.isPressed || kb.downArrowKey.isPressed) v.y -= 1f;
#elif SEASONS_OLD_INPUT
            if (Input.GetKey(KeyCode.D) || Input.GetKey(KeyCode.RightArrow)) v.x += 1f;
            if (Input.GetKey(KeyCode.A) || Input.GetKey(KeyCode.LeftArrow)) v.x -= 1f;
            if (Input.GetKey(KeyCode.W) || Input.GetKey(KeyCode.UpArrow)) v.y += 1f;
            if (Input.GetKey(KeyCode.S) || Input.GetKey(KeyCode.DownArrow)) v.y -= 1f;
#endif
            return v;
        }
    }
}
