// Wind-animated PBR for the season tiles' plants (built-in render pipeline).
// Trees bend with height above their base, grass and reeds bend along the blade (UV v = root -> tip),
// flower heads ride on their stems, and leaf cards flutter on top. Wind direction, strength, gusts and
// time come from SeasonsWind.cs through global shader properties.
Shader "Seasons/Wind Foliage"
{
    Properties
    {
        _Color ("Color", Color) = (1, 1, 1, 1)
        _MainTex ("Albedo (RGB) Alpha (A)", 2D) = "white" {}
        _Cutoff ("Alpha Cutoff", Range(0, 1)) = 0.5
        [NoScaleOffset] _BumpMap ("Normal Map", 2D) = "bump" {}
        _BumpScale ("Normal Scale", Float) = 1
        _Glossiness ("Smoothness", Range(0, 1)) = 0.2
        _Metallic ("Metallic", Range(0, 1)) = 0
        [Enum(UnityEngine.Rendering.CullMode)] _Cull ("Cull", Float) = 0

        [Header(Wind)]
        [Enum(Height, 0, UV, 1, Constant, 2)] _WeightMode ("Bend Weight From", Float) = 0
        _WindHeight ("Full-Bend Height (object Y, m)", Float) = 5
        _UVRef ("Full-Bend UV v", Float) = 1
        _BendPower ("Bend Curve", Float) = 2
        _BendAmount ("Bend at Full Weight (m)", Float) = 0.2
        _Flutter ("Leaf Flutter (m)", Float) = 0.02
        _FlutterFreq ("Leaf Flutter Frequency", Float) = 7
    }

    SubShader
    {
        Tags { "Queue" = "AlphaTest" "RenderType" = "TransparentCutout" "DisableBatching" = "True" }
        LOD 300
        Cull [_Cull]

        CGPROGRAM
        #pragma surface surf Standard vertex:vert addshadow fullforwardshadows alphatest:_Cutoff
        #pragma multi_compile_local __ _NORMALMAP
        #pragma target 3.0

        sampler2D _MainTex;
        sampler2D _BumpMap;
        fixed4 _Color;
        half _BumpScale;
        half _Glossiness;
        half _Metallic;
        float _WeightMode, _WindHeight, _UVRef, _BendPower, _BendAmount, _Flutter, _FlutterFreq;

        // Set every frame by SeasonsWind.cs
        float4 _SeasonsWind;       // xy: direction the wind blows towards (world XZ), z: strength, w: gust 0..1
        float _SeasonsWindTime;    // wind-speed-scaled time

        struct Input
        {
            float2 uv_MainTex;
            fixed facing : VFACE;
        };

        void vert(inout appdata_full v)
        {
            float w;
            if (_WeightMode < 0.5)
                w = pow(saturate(max(v.vertex.y, 0.0) / max(_WindHeight, 0.01)), _BendPower);
            else if (_WeightMode < 1.5)
                w = pow(saturate(v.texcoord.y / max(_UVRef, 0.001)), _BendPower);
            else
                w = 1.0;

            float3 wpos = mul(unity_ObjectToWorld, v.vertex).xyz;
            float2 dir = _SeasonsWind.xy;
            float strength = _SeasonsWind.z;
            float t = _SeasonsWindTime;

            // Main bend: leans downwind and rocks back, as a wave rolling across the scene with the wind.
            float wave = dot(wpos.xz, dir) * 0.35 + dot(wpos.xz, float2(0.13, 0.07));
            float sway = 0.6 + 0.3 * sin(t * 1.3 - wave) + 0.1 * sin(t * 3.1 - wave * 2.3);
            float bend = _BendAmount * strength * w * (sway + 0.8 * _SeasonsWind.w);
            float3 offset = float3(dir.x, 0.0, dir.y) * bend;

            // Flutter: each leaf card shivers along its normal.
            float3 n = UnityObjectToWorldNormal(v.normal);
            float ph = dot(wpos, float3(2.7, 1.9, 3.3));
            float flutter = sin(t * _FlutterFreq + ph) * cos(t * _FlutterFreq * 0.61 + ph * 1.7);
            offset += n * (flutter * _Flutter * (0.3 + strength) * sqrt(w));

            v.vertex.xyz += mul((float3x3)unity_WorldToObject, offset);
        }

        void surf(Input IN, inout SurfaceOutputStandard o)
        {
            fixed4 c = tex2D(_MainTex, IN.uv_MainTex) * _Color;
            o.Albedo = c.rgb;
            o.Alpha = c.a;
            o.Metallic = _Metallic;
            o.Smoothness = _Glossiness;
        #ifdef _NORMALMAP
            float3 nt = tex2D(_BumpMap, IN.uv_MainTex).xyz * 2.0 - 1.0;   // glTF normal maps are plain RGB
            nt.xy *= _BumpScale;
            nt.z = sqrt(saturate(1.0 - dot(nt.xy, nt.xy)));
        #else
            float3 nt = float3(0.0, 0.0, 1.0);
        #endif
            nt.z *= IN.facing > 0 ? 1.0 : -1.0;   // light the back of double-sided leaves and blades correctly
            o.Normal = nt;
        }
        ENDCG
    }
    FallBack "Legacy Shaders/Transparent/Cutout/VertexLit"
}
