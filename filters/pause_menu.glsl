uniform sampler2D bgl_RenderedTexture;

/*
vec4 contrast( in vec4 value , in float fac)
{	
	float m = max(max(value.x, value.y), value.z);
	value.x -= (m-value.x)*fac;
	value.y -= (m-value.y)*fac;
	value.z -= (m-value.z)*fac;
	
	return value;
}
*/

void main(void)
{
	vec4 color = texture2D(bgl_RenderedTexture, gl_TexCoord[0].st);
	gl_FragColor = color * (1- sqrt(pow(gl_TexCoord[0].st.x-0.5, 2) + pow(gl_TexCoord[0].st.y-0.5, 2)));
}