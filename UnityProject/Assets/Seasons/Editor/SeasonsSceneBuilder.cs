using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;

namespace RealisticSeasons.EditorTools
{
    /// <summary>
    /// Builds Assets/Seasons/Scenes/Seasons.unity from the two GLBs: the four season tiles, the props pack,
    /// a sun, an orbit camera, the SeasonSwitcher and SeasonsWind (plants move in the wind). Runs once
    /// automatically after the GLBs have been imported (glTFast), and on demand from the menu:
    /// Seasons > Build Demo Scene.
    /// </summary>
    static class SeasonsSceneBuilder
    {
        const string Root = "Assets/Seasons";
        const string TilesPath = Root + "/Models/realistic_seasons.glb";
        const string PropsPath = Root + "/Models/realistic_props.glb";
        const string SceneDir = Root + "/Scenes";
        internal const string ScenePath = SceneDir + "/Seasons.unity";
        static readonly Vector3 PropsOffset = new Vector3(30f, 0f, -15f);   // beside the tiles, not on top of them

        [MenuItem("Seasons/Build Demo Scene")]
        static void BuildFromMenu() => Build();

        [MenuItem("Seasons/Open Demo Scene")]
        static void OpenScene()
        {
            if (!File.Exists(ScenePath))
            {
                Build();
                return;
            }
            if (EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo())
                EditorSceneManager.OpenScene(ScenePath);
        }

        [InitializeOnLoadMethod]
        static void AutoBuildOnce()
        {
            if (Application.isBatchMode) return;
            EditorApplication.delayCall += () =>
            {
                string key = "RealisticSeasons.AutoBuilt." + Application.dataPath;
                if (EditorPrefs.GetBool(key, false) || EditorApplication.isPlayingOrWillChangePlaymode) return;
                if (File.Exists(ScenePath))
                {
                    EditorPrefs.SetBool(key, true);
                    return;
                }
                if (AssetDatabase.LoadAssetAtPath<GameObject>(TilesPath) == null) return;   // glTFast not done yet
                if (Build()) EditorPrefs.SetBool(key, true);
            };
        }

        internal static bool Build()
        {
            var tilesAsset = AssetDatabase.LoadAssetAtPath<GameObject>(TilesPath);
            if (tilesAsset == null)
            {
                EditorUtility.DisplayDialog("Seasons",
                    $"{TilesPath} has not been imported as a model.\n\n" +
                    "Install glTFast (Window > Package Manager > + > Add package by name > com.unity.cloud.gltfast) " +
                    "and run Seasons > Build Demo Scene again.", "OK");
                return false;
            }
            var propsAsset = AssetDatabase.LoadAssetAtPath<GameObject>(PropsPath);
            if (!EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo()) return false;

            if (PlayerSettings.colorSpace != ColorSpace.Linear)
                PlayerSettings.colorSpace = ColorSpace.Linear;      // the textures and lighting were authored for linear PBR
            QualitySettings.shadows = ShadowQuality.All;
            QualitySettings.shadowResolution = ShadowResolution.VeryHigh;
            QualitySettings.shadowCascades = 4;
            QualitySettings.shadowDistance = Mathf.Max(QualitySettings.shadowDistance, 90f);

            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);

            GameObject tiles = Spawn(tilesAsset, "Seasons_Tiles");
            GameObject props = propsAsset != null ? Spawn(propsAsset, "Seasons_Props") : null;
            if (props != null)
            {
                props.transform.position = PropsOffset;
                foreach (var lamp in props.GetComponentsInChildren<Light>(true).Where(x => x.type == LightType.Point))
                {
                    lamp.intensity = 1.5f;
                    lamp.range = 7f;
                    lamp.shadows = LightShadows.Soft;
                }
            }

            var sunGo = new GameObject("Sun");
            var sun = sunGo.AddComponent<Light>();
            sun.type = LightType.Directional;
            sun.shadows = LightShadows.Soft;
            sun.shadowStrength = 0.85f;
            sun.shadowNormalBias = 0.3f;

            var camGo = new GameObject("Main Camera") { tag = "MainCamera" };
            var cam = camGo.AddComponent<Camera>();
            cam.fieldOfView = 40f;
            cam.nearClipPlane = 0.05f;
            cam.farClipPlane = 600f;
            cam.allowHDR = true;
            camGo.AddComponent<AudioListener>();
            var orbit = camGo.AddComponent<OrbitCamera>();

            RenderSettings.skybox = AssetDatabase.GetBuiltinExtraResource<Material>("Default-Skybox.mat");
            RenderSettings.sun = sun;
            RenderSettings.ambientMode = AmbientMode.Trilight;

            var switcher = new GameObject("Season Switcher").AddComponent<SeasonSwitcher>();
            switcher.tilesRoot = tiles.transform;
            switcher.propsRoot = props != null ? props.transform : null;
            switcher.sun = sun;
            switcher.orbit = orbit;
            var wind = switcher.gameObject.AddComponent<SeasonsWind>();
            wind.windShader = Shader.Find("Seasons/Wind Foliage");
            wind.roots = props != null ? new[] { tiles.transform, props.transform } : new[] { tiles.transform };
            switcher.wind = wind;
            switcher.ApplyLighting(switcher.lighting[4]);   // so the scene already looks right in edit mode
            camGo.transform.SetPositionAndRotation(new Vector3(-8f, 15f, 28f), Quaternion.Euler(28f, 200f, 0f));

            Directory.CreateDirectory(SceneDir);
            if (!EditorSceneManager.SaveScene(scene, ScenePath)) return false;
            AssetDatabase.Refresh();

            var scenes = EditorBuildSettings.scenes.ToList();
            if (!scenes.Any(s => s.path == ScenePath))
            {
                scenes.Insert(0, new EditorBuildSettingsScene(ScenePath, true));
                EditorBuildSettings.scenes = scenes.ToArray();
            }
            Selection.activeGameObject = switcher.gameObject;
            Debug.Log($"Seasons: built {ScenePath}. Press Play, then 1-4 / 0 / P to switch views, Z / X for wind.");
            return true;
        }

        /// <summary>Instantiate an imported GLB and switch off the camera and sun that came along with it.</summary>
        static GameObject Spawn(GameObject asset, string name)
        {
            var go = PrefabUtility.InstantiatePrefab(asset) as GameObject;
            if (go == null) go = Object.Instantiate(asset);
            go.name = name;
            foreach (var c in go.GetComponentsInChildren<Camera>(true))
                c.gameObject.SetActive(false);
            foreach (var sun in go.GetComponentsInChildren<Light>(true).Where(x => x.type == LightType.Directional))
                sun.gameObject.SetActive(false);
            return go;
        }
    }
}
