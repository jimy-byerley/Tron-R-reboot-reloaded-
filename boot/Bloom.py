uniform sampler2D bgl_RenderedTexture;

#define color_fac 2.0
#define glow_radius 0.0018

void main()
{
    vec4 sum = vec4(0);
    vec2 texcoord = vec2(gl_TexCoord[0]).st;
    int j;
    int i;

    j = 0;
    for( i= -5; i < 5; i++)
    {
        sum += texture2D(bgl_RenderedTexture, texcoord + vec2(j, i)*glow_radius) * color_fac; 
    }
    
    i = 0;
    for (j = -5; j < 5; j++)
    {
        sum += texture2D(bgl_RenderedTexture, texcoord + vec2(j, i)*glow_radius) * color_fac; 
    }
    

    gl_FragColor = sum*sum*0.0020+texture2D(bgl_RenderedTexture, texcoord);
}