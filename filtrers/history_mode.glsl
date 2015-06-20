uniform sampler2D bgl_RenderedTexture;


#define MIN(a,b) (a>b)?b:a
#define MAX(a,b) (a>b)?a:b
vec4 uncontrast( in vec4 value )
{
	static float fac = 0.8;
	
	static float max = MAX(MAX(value.x, value.y), value.z);
	value.x += (max-value.x)*fac;
	value.y += (max-value.y)*fac;
	value.z += (max-value.z)*fac;
	
	return value;
}

/*
void main(void)
{
	// RGB diffraction
	vec2 basecoord = (gl_TexCoord[0].st-vec2(0.5)) * vec2(0.7,1);
	float red = uncontrast(texture2D(bgl_RenderedTexture, basecoord + vec2(0.497))).x;
	float green = uncontrast(texture2D(bgl_RenderedTexture, basecoord + vec2(0.5))).y;
	float blue = uncontrast(texture2D(bgl_RenderedTexture, basecoord + vec2(0.503))).z;
	// intensity is low on the center of the screen
	vec2 dist = abs(gl_TexCoord[0].st - vec2(0.5));
	float fac = pow(max(dist.x, dist.y),2)*2;
	vec4 pix = vec4(red, green, blue, 1);
	// add to original pixel

	vec4 value = texture2D(bgl_RenderedTexture, gl_TexCoord[0].st);
	gl_FragColor = min(vec4(1), value + pow(pix,4)*fac);
}
*/

#define PI 3.141592

void main(void)
{
	vec2 linear = (gl_TexCoord[0].st - vec2(0.5))*2;   // map coords on interval [0,1]
	vec2 sinus = sin(linear*PI/2) * 2/PI;              // map on sin function
	vec2 contrast;
	if (linear.x >0)    contrast.x = linear.x - pow(linear.x-sinus.x, 2);
	else                contrast.x = linear.x + pow(linear.x-sinus.x, 2);
	if (linear.y >0)    contrast.y = linear.y - pow(linear.y-sinus.y, 2);
	else                contrast.y = linear.y + pow(linear.y-sinus.y, 2);
	vec4 color = texture2D(bgl_RenderedTexture, contrast*0.5 + vec2(0.5));
	color.r = texture2D(bgl_RenderedTexture, contrast*0.503 + vec2(0.5)).r;
	color.b = texture2D(bgl_RenderedTexture, contrast*0.497 + vec2(0.5)).b;
	gl_FragColor = color;
}