using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;

namespace RealisticSeasons
{
    /// <summary>
    /// Makes the plants in the season tiles and props move in the wind.
    /// On start-up every tree, leaf, grass, reed and flower renderer under <see cref="roots"/> gets a copy of its
    /// glTF material on the "Seasons/Wind Foliage" shader (same textures); after that this component only feeds
    /// direction, strength and gusts to the shader each frame. Keys: Z / X = weaker / stronger wind.
    /// </summary>
    public class SeasonsWind : MonoBehaviour
    {
        [Tooltip("Seasons/Wind Foliage. Assigned by the scene builder so it is included in builds.")]
        public Shader windShader;
        [Tooltip("Instances of realistic_seasons.glb and realistic_props.glb.")]
        public Transform[] roots;

        [Header("Wind")]
        [Range(0f, 3f)] public float strength = 1f;
        [Tooltip("Direction the wind blows towards, degrees around +Y (0 = +Z).")]
        public float direction = 60f;
        [Range(0.2f, 3f)] public float speed = 1f;
        [Range(0f, 1f)] public float gustiness = 0.6f;
        [Tooltip("Strength multiplier per season: spring, summer, autumn, winter.")]
        public float[] seasonStrength = { 0.9f, 0.7f, 1.3f, 0.8f };

        static readonly int WindId = Shader.PropertyToID("_SeasonsWind");
        static readonly int WindTimeId = Shader.PropertyToID("_SeasonsWindTime");
        static readonly int HeightId = Shader.PropertyToID("_WindHeight");
        static readonly int BendId = Shader.PropertyToID("_BendAmount");

        float seasonFactor = 1f, current, windTime;
        readonly Dictionary<(Material, string), Material> variants = new Dictionary<(Material, string), Material>();

        /// <summary>How a renderer (or one of its sub-meshes) moves.</summary>
        struct Profile
        {
            public string key;
            public int mode;            // 0 = height above base, 1 = UV v along the blade, 2 = whole piece
            public float uvRef, power, bend, flutter, freq;
            public bool doubleSided;
            public bool perTreeBend;    // bend = bendPerMetre * tree height, set per renderer
        }

        public void SetSeason(Season season) => seasonFactor = seasonStrength[(int)season];
        public void SetNeutral() => seasonFactor = 1f;

        void Start()   // Start, not Awake: roots may be assigned right after AddComponent
        {
            if (windShader == null) windShader = Shader.Find("Seasons/Wind Foliage");
            if (windShader == null)
            {
                Debug.LogWarning("SeasonsWind: shader 'Seasons/Wind Foliage' not found, wind disabled.", this);
                enabled = false;
                return;
            }
            current = strength;
            if (roots == null) return;
            foreach (Transform root in roots)
                if (root != null) Apply(root);
        }

        void Update()
        {
            if (InputCompat.LetterDown('X')) strength = Mathf.Min(strength + 0.25f, 3f);
            if (InputCompat.LetterDown('Z')) strength = Mathf.Max(strength - 0.25f, 0f);

            current = Mathf.MoveTowards(current, strength * seasonFactor, Time.deltaTime * 0.5f);
            float t = Time.time;
            float gust = gustiness * Mathf.Clamp01(Mathf.PerlinNoise(t * 0.18f, 0.37f) * 1.8f - 0.6f);
            float yaw = (direction + (Mathf.PerlinNoise(t * 0.05f, 4.2f) - 0.5f) * 40f) * Mathf.Deg2Rad;
            windTime += Time.deltaTime * speed * (0.7f + 0.5f * current + gust);

            Shader.SetGlobalVector(WindId, new Vector4(Mathf.Sin(yaw), Mathf.Cos(yaw), current, gust));
            Shader.SetGlobalFloat(WindTimeId, windTime);
        }

        void OnDisable()
        {
            Shader.SetGlobalVector(WindId, Vector4.zero);
        }

        void Apply(Transform root)
        {
            var renderers = root.GetComponentsInChildren<MeshRenderer>(true);
            // Branches and their leaves are separate objects: give both the height of the taller one so they bend together.
            var treeHeight = new Dictionary<string, float>();
            foreach (MeshRenderer r in renderers)
            {
                string tree = TreeKey(r.transform);
                if (tree == null) continue;
                float top = ObjectTop(r);
                treeHeight[tree] = treeHeight.TryGetValue(tree, out float h) ? Mathf.Max(h, top) : top;
            }

            var block = new MaterialPropertyBlock();
            foreach (MeshRenderer r in renderers)
            {
                Material[] mats = r.sharedMaterials;
                bool changed = false, perTree = false;
                float bendPerMetre = 0f;
                for (int i = 0; i < mats.Length; i++)
                {
                    if (mats[i] == null || !TryProfile(r.transform, mats[i], out Profile p)) continue;
                    mats[i] = Variant(mats[i], p);
                    changed = true;
                    if (p.perTreeBend)
                    {
                        perTree = true;
                        bendPerMetre = p.bend;
                    }
                }
                if (!changed) continue;
                r.sharedMaterials = mats;
                if (perTree)
                {
                    string tree = TreeKey(r.transform);
                    float height = tree != null && treeHeight.TryGetValue(tree, out float h) ? h : ObjectTop(r);
                    r.GetPropertyBlock(block);
                    block.SetFloat(HeightId, height);
                    block.SetFloat(BendId, bendPerMetre * height);
                    r.SetPropertyBlock(block);
                }
            }
        }

        /// <summary>Decide from object and material names (they come straight from the Blender scene).</summary>
        static bool TryProfile(Transform t, Material mat, out Profile p)
        {
            p = default;
            string n = NameChain(t);
            string m = mat.name.ToLowerInvariant();
            bool clip = IsAlphaClipped(mat);
            if (n.Contains("fallen")) return false;                        // leaves and petals lying on the ground

            if (n.Contains("spruce"))
            {
                p = new Profile { key = "spruce", mode = 0, power = 2.2f, bend = 0.03f, perTreeBend = true,
                                  flutter = clip ? 0.006f : 0f, freq = 9f, doubleSided = clip };
                return true;
            }
            if (n.Contains("leaves"))
            {
                p = new Profile { key = "leaves", mode = 0, power = 2f, bend = 0.045f, perTreeBend = true,
                                  flutter = 0.03f, freq = 7f, doubleSided = true };
                return true;
            }
            if (n.Contains("cherrytree") || (n.Contains("branches") && (n.Contains("birch") || n.Contains("shrub"))))
            {
                p = new Profile { key = "branches", mode = 0, power = 2f, bend = 0.045f, perTreeBend = true };
                return true;
            }
            if (n.Contains("grass") || n.Contains("reeds"))
            {
                bool reeds = n.Contains("reeds");
                p = new Profile { key = reeds ? "reeds" : "grass", mode = 1, uvRef = 1f, power = 1.5f,
                                  bend = reeds ? 0.12f : 0.07f, flutter = 0.01f, freq = 5f, doubleSided = true };
                return true;
            }
            if (n.Contains("flowerstems"))
            {
                p = new Profile { key = "stems", mode = 1, uvRef = 0.12f, power = 1f, bend = 0.035f };
                return true;
            }
            if (n.Contains("flowers"))
            {
                p = new Profile { key = "heads", mode = 2, power = 1f, bend = 0.035f, flutter = 0.006f, freq = 6f,
                                  doubleSided = true };
                return true;
            }
            if (n.Contains("cattails"))
            {
                bool head = m.Contains("cattail");
                p = new Profile { key = head ? "cattail" : "stalk", mode = head ? 2 : 1, uvRef = 0.15f, power = 1f,
                                  bend = 0.06f };
                return true;
            }
            return false;
        }

        Material Variant(Material src, Profile p)
        {
            var key = (src, p.key);
            if (variants.TryGetValue(key, out Material cached)) return cached;

            bool clip = IsAlphaClipped(src);
            var m = new Material(windShader) { name = src.name + " (Wind)" };
            string tex = First(src, "baseColorTexture", "_BaseMap", "_MainTex", "_BaseColorMap");
            if (tex != null)
            {
                m.SetTexture("_MainTex", src.GetTexture(tex));
                m.SetTextureScale("_MainTex", src.GetTextureScale(tex));
                m.SetTextureOffset("_MainTex", src.GetTextureOffset(tex));
            }
            string col = First(src, "baseColorFactor", "_BaseColor", "_Color");
            if (col != null) m.SetColor("_Color", src.GetColor(col));
            string nrm = First(src, "normalTexture", "_BumpMap", "_NormalMap");
            if (nrm != null && src.GetTexture(nrm) != null)
            {
                m.SetTexture("_BumpMap", src.GetTexture(nrm));
                m.EnableKeyword("_NORMALMAP");
                string scale = First(src, "normalTexture_scale", "_BumpScale", "_NormalScale");
                if (scale != null) m.SetFloat("_BumpScale", src.GetFloat(scale));
            }
            string cutoff = First(src, "alphaCutoff", "_Cutoff", "_AlphaCutoff");
            m.SetFloat("_Cutoff", clip ? (cutoff != null ? src.GetFloat(cutoff) : 0.5f) : 0f);
            if (src.HasProperty("roughnessFactor")) m.SetFloat("_Glossiness", 1f - src.GetFloat("roughnessFactor"));
            else if (src.HasProperty("_Smoothness")) m.SetFloat("_Glossiness", src.GetFloat("_Smoothness"));
            if (src.HasProperty("metallicFactor")) m.SetFloat("_Metallic", src.GetFloat("metallicFactor"));
            else if (src.HasProperty("_Metallic")) m.SetFloat("_Metallic", src.GetFloat("_Metallic"));

            m.SetFloat("_Cull", (float)(p.doubleSided ? CullMode.Off : CullMode.Back));
            m.SetFloat("_WeightMode", p.mode);
            m.SetFloat("_UVRef", p.uvRef);
            m.SetFloat("_BendPower", p.power);
            m.SetFloat("_BendAmount", p.bend);   // per-tree renderers override this through a property block
            m.SetFloat("_Flutter", p.flutter);
            m.SetFloat("_FlutterFreq", p.freq);
            m.renderQueue = (int)RenderQueue.AlphaTest;
            variants[key] = m;
            return m;
        }

        static bool IsAlphaClipped(Material m) =>
            m.IsKeywordEnabled("_ALPHATEST_ON") ||
            (m.renderQueue >= (int)RenderQueue.AlphaTest && m.renderQueue < (int)RenderQueue.GeometryLast);

        static string First(Material m, params string[] names)
        {
            foreach (string n in names)
                if (m.HasProperty(n)) return n;
            return null;
        }

        /// <summary>Lower-case names of the renderer and its two parents (glTF importers may nest primitives).</summary>
        static string NameChain(Transform t)
        {
            string s = t.name;
            if (t.parent != null)
            {
                s += "/" + t.parent.name;
                if (t.parent.parent != null) s += "/" + t.parent.parent.name;
            }
            return s.ToLowerInvariant();
        }

        /// <summary>"Spring_CherryTree" for both Spring_CherryTree and Spring_CherryTree_Leaves, etc.</summary>
        static string TreeKey(Transform t)
        {
            for (int i = 0; i < 3 && t != null; i++, t = t.parent)
            {
                string n = t.name;
                if (n.EndsWith("_Leaves")) return n.Substring(0, n.Length - "_Leaves".Length);
                if (n.EndsWith("_Branches")) return n.Substring(0, n.Length - "_Branches".Length);
                if (n.Contains("CherryTree") || n.Contains("Spruce")) return n;
            }
            return null;
        }

        static float ObjectTop(MeshRenderer r)
        {
            var mf = r.GetComponent<MeshFilter>();
            return mf != null && mf.sharedMesh != null ? Mathf.Max(mf.sharedMesh.bounds.max.y, 0.3f) : 5f;
        }
    }
}
