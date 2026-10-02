using System.IO;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEngine;

namespace RealisticSeasons.EditorTools
{
    /// <summary>
    /// Builds a playable game for the computer you run it on, from the editor menu (Seasons > Build Game) or a terminal:
    ///   Unity -batchmode -quit -projectPath &lt;UnityProject&gt; -executeMethod RealisticSeasons.EditorTools.SeasonsBuild.Build
    /// Output: Builds/Windows/Seasons.exe, Builds/Mac/Seasons.app or Builds/Linux/Seasons.x86_64 inside the project folder.
    /// </summary>
    public static class SeasonsBuild
    {
        [MenuItem("Seasons/Build Game")]
        public static void Build()
        {
            bool ok = File.Exists(SeasonsSceneBuilder.ScenePath) || SeasonsSceneBuilder.Build();
            if (ok)
            {
                BuildTarget target;
                string path;
                switch (Application.platform)
                {
                    case RuntimePlatform.OSXEditor:
                        target = BuildTarget.StandaloneOSX;
                        path = "Builds/Mac/Seasons.app";
                        break;
                    case RuntimePlatform.LinuxEditor:
                        target = BuildTarget.StandaloneLinux64;
                        path = "Builds/Linux/Seasons.x86_64";
                        break;
                    default:
                        target = BuildTarget.StandaloneWindows64;
                        path = "Builds/Windows/Seasons.exe";
                        break;
                }

                PlayerSettings.productName = "Seasons";
                PlayerSettings.fullScreenMode = FullScreenMode.Windowed;
                PlayerSettings.defaultScreenWidth = 1600;
                PlayerSettings.defaultScreenHeight = 900;
                PlayerSettings.resizableWindow = true;

                BuildReport report = BuildPipeline.BuildPlayer(new BuildPlayerOptions
                {
                    scenes = new[] { SeasonsSceneBuilder.ScenePath },
                    locationPathName = path,
                    target = target,
                    options = BuildOptions.None,
                });
                ok = report.summary.result == BuildResult.Succeeded;
                Debug.Log(ok ? $"Seasons: game built -> {Path.GetFullPath(path)}"
                             : $"Seasons: build failed ({report.summary.result}), see the errors above.");
                if (ok && !Application.isBatchMode) EditorUtility.RevealInFinder(path);
            }
            else
            {
                Debug.LogError("Seasons: could not create the demo scene (are the .glb files imported? see above).");
            }
            if (Application.isBatchMode) EditorApplication.Exit(ok ? 0 : 1);
        }
    }
}
