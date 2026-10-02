using UnityEngine;

namespace RealisticSeasons
{
    /// <summary>
    /// Orbit / pan / zoom camera for looking around the season tiles and props.
    /// Right (or left) drag: orbit · Middle drag or Shift + drag: pan · Wheel: zoom · WASD / arrows: move the focus.
    /// </summary>
    [RequireComponent(typeof(Camera))]
    public class OrbitCamera : MonoBehaviour
    {
        public Vector3 target = new Vector3(0f, 1f, 0f);
        public float distance = 30f;
        public float yaw = 200f;
        [Range(-10f, 89f)] public float pitch = 26f;

        [Header("Limits")]
        public float minDistance = 1.5f;
        public float maxDistance = 150f;

        [Header("Feel")]
        [Tooltip("Degrees per pixel of mouse movement.")]
        public float orbitSpeed = 0.25f;
        [Tooltip("Fraction of the distance per wheel notch.")]
        public float zoomStep = 0.12f;
        public float panSpeed = 1f;
        public float smoothTime = 0.25f;

        Vector3 goalTarget;
        float goalDistance, goalYaw, goalPitch;
        Vector3 targetVel;
        float distanceVel, yawVel, pitchVel;
        Vector2 lastMouse;
        bool dragging;

        void Awake()
        {
            goalTarget = target;
            goalDistance = distance;
            goalYaw = yaw;
            goalPitch = pitch;
            Apply();
        }

        /// <summary>Glide (or jump, with snap) to look at a new point.</summary>
        public void FocusOn(Vector3 center, float newDistance, float newYaw, float newPitch, bool snap = false)
        {
            goalTarget = center;
            goalDistance = Mathf.Clamp(newDistance, minDistance, maxDistance);
            goalYaw = newYaw;
            goalPitch = Mathf.Clamp(newPitch, -10f, 89f);
            if (!snap) return;
            target = goalTarget;
            distance = goalDistance;
            yaw = goalYaw;
            pitch = goalPitch;
            targetVel = Vector3.zero;
            distanceVel = yawVel = pitchVel = 0f;
            Apply();
        }

        void LateUpdate()
        {
            Vector2 mouse = InputCompat.MousePosition();
            Vector2 delta = dragging ? mouse - lastMouse : Vector2.zero;
            bool shift = InputCompat.ShiftHeld();
            bool left = InputCompat.Held(InputCompat.Button.Left);
            bool orbit = InputCompat.Held(InputCompat.Button.Right) || (left && !shift);
            bool pan = InputCompat.Held(InputCompat.Button.Middle) || (left && shift);
            dragging = orbit || pan;
            lastMouse = mouse;

            if (orbit)
            {
                goalYaw += delta.x * orbitSpeed;
                goalPitch = Mathf.Clamp(goalPitch - delta.y * orbitSpeed, -10f, 89f);
            }
            if (pan)
            {
                float k = goalDistance * 0.0015f * panSpeed;
                goalTarget -= Quaternion.Euler(goalPitch, goalYaw, 0f) * new Vector3(delta.x * k, delta.y * k, 0f);
            }

            Vector2 move = InputCompat.Move();
            if (move != Vector2.zero)
            {
                Quaternion heading = Quaternion.Euler(0f, goalYaw, 0f);
                Vector3 step = heading * new Vector3(move.x, 0f, move.y);
                goalTarget += step * (goalDistance * 0.6f * panSpeed * Time.unscaledDeltaTime);
            }

            float scroll = InputCompat.Scroll();
            if (scroll != 0f)
                goalDistance = Mathf.Clamp(goalDistance * Mathf.Pow(1f - zoomStep, scroll), minDistance, maxDistance);

            float dt = Time.unscaledDeltaTime;
            target = Vector3.SmoothDamp(target, goalTarget, ref targetVel, smoothTime, Mathf.Infinity, dt);
            distance = Mathf.SmoothDamp(distance, goalDistance, ref distanceVel, smoothTime, Mathf.Infinity, dt);
            yaw = Mathf.SmoothDampAngle(yaw, goalYaw, ref yawVel, smoothTime * 0.5f, Mathf.Infinity, dt);
            pitch = Mathf.SmoothDampAngle(pitch, goalPitch, ref pitchVel, smoothTime * 0.5f, Mathf.Infinity, dt);
            Apply();
        }

        void Apply()
        {
            Quaternion rot = Quaternion.Euler(pitch, yaw, 0f);
            transform.SetPositionAndRotation(target + rot * new Vector3(0f, 0f, -distance), rot);
        }
    }
}
