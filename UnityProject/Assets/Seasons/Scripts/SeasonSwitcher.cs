using UnityEngine;
using UnityEngine.Rendering;

namespace RealisticSeasons
{
    public enum Season { Spring, Summer, Autumn, Winter }

    /// <summary>Sun, ambient, sky and fog settings for one season (or the overview).</summary>
    [System.Serializable]
    public class SeasonLighting
    {
        public string label;
        [Range(0f, 90f)] public float sunElevation = 40f;
        [Tooltip("0 = in front of the tile, positive = to the right (same convention as the Blender generator).")]
        [Range(-180f, 180f)] public float sunAzimuth = 45f;
        public float sunIntensity = 1.25f;
        public Color sunColor = Color.white;
        public Color skyAmbient = new Color(0.62f, 0.68f, 0.78f);
        public Color equatorAmbient = new Color(0.55f, 0.57f, 0.54f);
        public Color groundAmbient = new Color(0.30f, 0.28f, 0.24f);
        [Tooltip("Procedural skybox atmosphere thickness (haze).")]
        [Range(0f, 5f)] public float atmosphere = 1f;
        public Color fogColor = new Color(0.74f, 0.80f, 0.88f);
        [Range(0f, 0.05f)] public float fogDensity = 0.003f;

        public SeasonLighting() { }

        public SeasonLighting(string label, float elevation, float azimuth, float intensity, string sunHex,
                              Color sky, Color equator, Color ground, float atmosphere, Color fog, float fogDensity)
        {
            this.label = label;
            sunElevation = elevation;
            sunAzimuth = azimuth;
            sunIntensity = intensity;
            ColorUtility.TryParseHtmlString(sunHex, out sunColor);
            skyAmbient = sky;
            equatorAmbient = equator;
            groundAmbient = ground;
            this.atmosphere = atmosphere;
            fogColor = fog;
            this.fogDensity = fogDensity;
        }
    }

    /// <summary>
    /// Shows one season tile, all four side by side, or the props showcase, and relights the scene to match
    /// (and tells <see cref="SeasonsWind"/> how windy the season is).
    /// Keys: 1 spring · 2 summer · 3 autumn · 4 winter · 0 all four · P props · H toggle help.
    /// Tiles are found by their node names in realistic_seasons.glb (Spring_Tile, Summer_Tile, ...).
    /// </summary>
    public class SeasonSwitcher : MonoBehaviour
    {
        public Transform tilesRoot;
        public Transform propsRoot;
        public Light sun;
        public OrbitCamera orbit;
        public SeasonsWind wind;
        public bool startWithOverview = true;
        public Season startSeason = Season.Spring;
        public bool showHelp = true;

        [Tooltip("Spring, Summer, Autumn, Winter, Overview")]
        public SeasonLighting[] lighting = DefaultLighting();

        const int Overview = 4;
        const float TileYaw = 212f, TilePitch = 22f, TileDistance = 13f;   // matches the Blender tile renders

        readonly Transform[] tiles = new Transform[4];
        Material skyInstance;
        GUIStyle helpStyle;
        string status = "";

        public static SeasonLighting[] DefaultLighting() => new[]
        {
            new SeasonLighting("Spring", 40f, 55f, 1.25f, "#FFF4E6", new Color(0.62f, 0.68f, 0.78f),
                new Color(0.55f, 0.58f, 0.53f), new Color(0.30f, 0.28f, 0.23f), 1.0f, new Color(0.74f, 0.80f, 0.88f), 0.003f),
            new SeasonLighting("Summer", 58f, 40f, 1.45f, "#FFFAF0", new Color(0.60f, 0.68f, 0.84f),
                new Color(0.52f, 0.58f, 0.50f), new Color(0.28f, 0.29f, 0.22f), 0.8f, new Color(0.72f, 0.80f, 0.90f), 0.002f),
            new SeasonLighting("Autumn", 16f, 70f, 1.15f, "#FFCB94", new Color(0.58f, 0.56f, 0.62f),
                new Color(0.62f, 0.50f, 0.40f), new Color(0.30f, 0.24f, 0.18f), 1.6f, new Color(0.80f, 0.72f, 0.64f), 0.005f),
            new SeasonLighting("Winter", 19f, 60f, 0.85f, "#E8F0FF", new Color(0.70f, 0.76f, 0.88f),
                new Color(0.62f, 0.66f, 0.74f), new Color(0.52f, 0.54f, 0.58f), 3.0f, new Color(0.82f, 0.86f, 0.92f), 0.007f),
            new SeasonLighting("Overview", 40f, 45f, 1.25f, "#FFF6EC", new Color(0.62f, 0.68f, 0.78f),
                new Color(0.55f, 0.57f, 0.54f), new Color(0.30f, 0.28f, 0.24f), 1.0f, new Color(0.74f, 0.80f, 0.88f), 0.002f),
        };

        void Awake()
        {
            if (tilesRoot != null)
            {
                for (int i = 0; i < 4; i++)
                {
                    tiles[i] = FindDeep(tilesRoot, (Season)i + "_Tile");
                    if (tiles[i] == null)
                        Debug.LogWarning($"SeasonSwitcher: '{(Season)i}_Tile' not found under {tilesRoot.name}", this);
                }
            }
            if (RenderSettings.skybox != null)
            {
                skyInstance = new Material(RenderSettings.skybox);   // tint a copy, never the project asset
                RenderSettings.skybox = skyInstance;
            }
            if (sun != null)
                RenderSettings.sun = sun;
            if (wind == null)
                wind = GetComponent<SeasonsWind>();
            if (wind == null && tilesRoot != null)   // scene built before wind existed
            {
                wind = gameObject.AddComponent<SeasonsWind>();
                wind.roots = propsRoot != null ? new[] { tilesRoot, propsRoot } : new[] { tilesRoot };
            }
        }

        void Start()
        {
            if (startWithOverview) ShowAll(true);
            else Show(startSeason, true);
        }

        void Update()
        {
            for (int d = 1; d <= 4; d++)
                if (InputCompat.DigitDown(d)) Show((Season)(d - 1));
            if (InputCompat.DigitDown(0)) ShowAll();
            if (InputCompat.LetterDown('P')) ShowProps();
            if (InputCompat.LetterDown('H')) showHelp = !showHelp;
            if (InputCompat.EscapeDown() && !Application.isEditor) Application.Quit();
        }

        /// <summary>Show a single season tile with its own lighting.</summary>
        public void Show(Season season, bool snap = false)
        {
            for (int i = 0; i < 4; i++)
                if (tiles[i] != null) tiles[i].gameObject.SetActive(i == (int)season);
            ApplyLighting(lighting[(int)season]);
            if (wind != null) wind.SetSeason(season);
            Transform t = tiles[(int)season];
            if (orbit != null && t != null)
                orbit.FocusOn(t.position + new Vector3(0f, 1.05f, -0.3f), TileDistance, TileYaw, TilePitch, snap);
            status = season.ToString();
        }

        /// <summary>Show all four tiles side by side.</summary>
        public void ShowAll(bool snap = false)
        {
            Vector3 center = Vector3.zero;
            int n = 0;
            foreach (Transform t in tiles)
            {
                if (t == null) continue;
                t.gameObject.SetActive(true);
                center += t.position;
                n++;
            }
            if (n > 0) center /= n;
            ApplyLighting(lighting[Overview]);
            if (wind != null) wind.SetNeutral();
            if (orbit != null)
                orbit.FocusOn(center + Vector3.up, 30f, 200f, 28f, snap);
            status = "All seasons";
        }

        /// <summary>Frame the props pack (birches, shrubs, cabin, well, bridge, small props).</summary>
        public void ShowProps(bool snap = false)
        {
            if (propsRoot == null) return;
            foreach (Transform t in tiles)
                if (t != null) t.gameObject.SetActive(true);
            ApplyLighting(lighting[Overview]);
            if (wind != null) wind.SetNeutral();
            Bounds b = WorldBounds(propsRoot);
            if (orbit != null)
                orbit.FocusOn(b.center, b.extents.magnitude * 1.8f, 200f, 30f, snap);
            status = "Props";
        }

        public void ApplyLighting(SeasonLighting l)
        {
            if (sun != null)
            {
                float e = l.sunElevation * Mathf.Deg2Rad, a = l.sunAzimuth * Mathf.Deg2Rad;
                // Blender (x, y, z) arrives in Unity as (-x, z, -y) through glTF, so the generator's
                // sun direction (cos e sin a, -cos e cos a, sin e) becomes:
                var toSun = new Vector3(-Mathf.Cos(e) * Mathf.Sin(a), Mathf.Sin(e), Mathf.Cos(e) * Mathf.Cos(a));
                sun.transform.rotation = Quaternion.LookRotation(-toSun);
                sun.color = l.sunColor;
                sun.intensity = l.sunIntensity;
            }
            RenderSettings.ambientMode = AmbientMode.Trilight;
            RenderSettings.ambientSkyColor = l.skyAmbient;
            RenderSettings.ambientEquatorColor = l.equatorAmbient;
            RenderSettings.ambientGroundColor = l.groundAmbient;
            RenderSettings.fog = l.fogDensity > 0f;
            RenderSettings.fogMode = FogMode.Exponential;
            RenderSettings.fogDensity = l.fogDensity;
            RenderSettings.fogColor = l.fogColor;
            if (skyInstance != null && skyInstance.HasProperty("_AtmosphereThickness"))
                skyInstance.SetFloat("_AtmosphereThickness", l.atmosphere);
        }

        void OnGUI()
        {
            if (!showHelp) return;
            if (helpStyle == null)
            {
                helpStyle = new GUIStyle(GUI.skin.box)
                {
                    alignment = TextAnchor.UpperLeft,
                    fontSize = 14,
                    padding = new RectOffset(10, 10, 8, 8),
                };
                helpStyle.normal.textColor = Color.white;
            }
            string windLine = wind != null && wind.enabled ? $"Wind {wind.strength:0.00}   Z / X: weaker / stronger" : "";
            GUI.Box(new Rect(12f, 12f, 640f, 92f),
                status + "\n1 Spring   2 Summer   3 Autumn   4 Winter   0 All   P Props   H Hide help   Esc Quit\n" +
                "Right/left drag: orbit   Middle or Shift+drag: pan   Wheel: zoom   WASD: move\n" + windLine, helpStyle);
        }

        static Transform FindDeep(Transform root, string name)
        {
            if (root.name == name) return root;
            foreach (Transform child in root)
            {
                Transform hit = FindDeep(child, name);
                if (hit != null) return hit;
            }
            return null;
        }

        static Bounds WorldBounds(Transform root)
        {
            Renderer[] rs = root.GetComponentsInChildren<Renderer>();
            if (rs.Length == 0) return new Bounds(root.position, Vector3.one);
            Bounds b = rs[0].bounds;
            foreach (Renderer r in rs) b.Encapsulate(r.bounds);
            return b;
        }
    }
}
