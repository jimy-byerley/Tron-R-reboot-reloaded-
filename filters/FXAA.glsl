#version 120

uniform sampler2D bgl_RenderedTexture;
uniform float bgl_RenderedTextureWidth;
uniform float bgl_RenderedTextureHeight;

float width = bgl_RenderedTextureWidth;
float height = bgl_RenderedTextureHeight;


float FXAA_SUBPIX_SHIFT = 1.0/4.0;
vec2 rcpFrame = vec2(1.0/width, 1.0/height);
vec4 posPos = vec4(gl_TexCoord[0].st,gl_TexCoord[0].st -(rcpFrame * (0.5 + FXAA_SUBPIX_SHIFT)));


vec3 FxaaPixelShader(
  vec4 posPos, // Output of FxaaVertexShader interpolated across screen.
  sampler2D tex, // Input texture.
  vec2 rcpFrame) // Constant {1.0/frameWidth, 1.0/frameHeight}.
{
/*---------------------------------------------------------*/
    #define FXAA_REDUCE_MIN   (1.0/128.0)
    #define FXAA_REDUCE_MUL   (1.0/8.0)
    #define FXAA_SPAN_MAX     8.0
/*---------------------------------------------------------*/
    vec3 rgbNW = texture2DLod(tex, posPos.zw, 0.0).xyz;
    vec3 rgbNE = texture2DLod(tex, posPos.zw + vec2(1.0,0.0)*rcpFrame.xy, 0.0).xyz;
    vec3 rgbSW = texture2DLod(tex, posPos.zw + vec2(0.0,1.0)*rcpFrame.xy, 0.0).xyz;
    vec3 rgbSE = texture2DLod(tex, posPos.zw + vec2(1.0,1.0)*rcpFrame.xy, 0.0).xyz;
    vec3 rgbM  = texture2DLod(tex, posPos.xy,0.0).xyz;
/*---------------------------------------------------------*/
    vec3 luma = vec3(0.299, 0.587, 0.114);
    float lumaNW = dot(rgbNW, luma);
    float lumaNE = dot(rgbNE, luma);
    float lumaSW = dot(rgbSW, luma);
    float lumaSE = dot(rgbSE, luma);
    float lumaM  = dot(rgbM,  luma);
/*---------------------------------------------------------*/
    float lumaMin = min(lumaM, min(min(lumaNW, lumaNE), min(lumaSW, lumaSE)));
    float lumaMax = max(lumaM, max(max(lumaNW, lumaNE), max(lumaSW, lumaSE)));
/*---------------------------------------------------------*/
    vec2 dir;
    dir.x = -((lumaNW + lumaNE) - (lumaSW + lumaSE));
    dir.y =  ((lumaNW + lumaSW) - (lumaNE + lumaSE));
/*---------------------------------------------------------*/
    float dirReduce = max(
        (lumaNW + lumaNE + lumaSW + lumaSE) * (0.25 * FXAA_REDUCE_MUL),
        FXAA_REDUCE_MIN);
    float rcpDirMin = 1.0/(min(abs(dir.x), abs(dir.y)) + dirReduce);
    dir = min(vec2( FXAA_SPAN_MAX,  FXAA_SPAN_MAX),
          max(vec2(-FXAA_SPAN_MAX, -FXAA_SPAN_MAX),
          dir * rcpDirMin)) * rcpFrame.xy;
/*--------------------------------------------------------*/
    vec3 rgbA = (1.0/2.0) * (
        texture2DLod(tex, posPos.xy + dir * (1.0/3.0 - 0.5),0.0).xyz +
        texture2DLod(tex, posPos.xy + dir * (2.0/3.0 - 0.5),0.0).xyz);
    vec3 rgbB = rgbA * (1.0/2.0) + (1.0/4.0) * (
        texture2DLod(tex, posPos.xy + dir * (0.0/3.0 - 0.5),0.0).xyz +
        texture2DLod(tex, posPos.xy + dir * (3.0/3.0 - 0.5),0.0).xyz);
    float lumaB = dot(rgbB, luma);
    if((lumaB < lumaMin) || (lumaB > lumaMax)) return rgbA;
    return rgbB; }

vec4 PostFX(sampler2D tex, vec2 uv)
{
  vec4 c = vec4(0.0);
  vec2 rcpFrame = vec2(1.0/width, 1.0/height);
  c.rgb = FxaaPixelShader(posPos, tex, rcpFrame);
  //c.rgb = 1.0 - texture2D(tex, posPos.xy).rgb;
  c.a = 1.0;
  return c;
}

void main()
{
  vec2 uv = gl_TexCoord[0].st;
  gl_FragColor = PostFX(bgl_RenderedTexture, uv);
}