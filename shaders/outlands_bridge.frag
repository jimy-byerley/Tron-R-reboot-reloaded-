varying vec3 T, B, N;
uniform sampler2D reflection, specular;

vec4 diffuse_color = vec4(0.007, 0.011, 0.011, 1.0);
vec4 specular_color = vec4(1.0);
float spec_size_1 = 1.0;
float spec_size_2 = 5.0;

int i,j;

void main() {

    vec2 coord = gl_TexCoord[1].xy/gl_TexCoord[1].w;

	vec4 glow = vec4(0);
	for (i=-2; i<2; i++)
	{
		for (j=-2; j<2; j++)
		{
			glow += texture2D(reflection, coord+vec2(j,i)*0.0016) /16.0;
		}
	}
	
    vec4 diffuse = gl_FrontLightProduct.diffuse * diffuse_color;
    vec4 specular = gl_FrontLightProduct.specular 
		* texture2D(specular, gl_TexCoord[0].st * spec_size_1) 
		* texture2D(specular, gl_TexCoord[0].st * spec_size_2);

    gl_FragColor = diffuse + specular + glow;
}
