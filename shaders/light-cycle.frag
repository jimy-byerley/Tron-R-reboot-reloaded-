uniform sampler2D diffuse;
uniform sampler2D specular;
uniform sampler2D normal;
uniform sampler2D emit;
uniform vec4 color;

varying vec3 N;
varying vec3 v;
varying vec4 vertex;

void main (void)
{
	// we are in Eye Coordinates, so EyePos is (0,0,0)
	int i;
	
	vec3 norm = N + 2.0*vec3(texture2D(normal,  gl_TexCoord[0].st)) - vec3(1);
	
	vec3 L;
	vec3 E = normalize(-v); // normalized vector from face to eye
	vec3 R;
	
	float quadraticAttenuation;
	
	vec4 spec = vec4(0.0);
	vec4 diff = vec4(0.0);
	
	for (i=0; i<1; i++)
	{
		L = normalize(gl_LightSource[i].position.xyz*gl_NormalMatrix - v); // normalized vector beetween light and face
		R = normalize(-reflect(L,norm));
		quadraticAttenuation = 0.5;// 1.0/ pow(length(gl_LightSource[i].position - v), 2.0);
		diff += gl_LightSource[i].diffuse  * max(dot(norm,L), 0.0) * quadraticAttenuation;
		spec += gl_LightSource[i].specular * pow(max(dot(R,E), 0.0), gl_FrontMaterial.shininess) * gl_FrontMaterial.specular * quadraticAttenuation;
	}
	diff = clamp(diff, 0.0, 1.0);
	
	//gl_FragColor = spec;
	/*
	gl_FragColor = gl_FrontMaterial.ambient
		+ diff  * vec4(norm, 1.0)  * gl_FrontMaterial.diffuse
		+ spec  * texture2D(specular, gl_TexCoord[0].st)
		+ color * texture2D(emit,     gl_TexCoord[0].st);
	*/
	/*
	gl_FragColor = gl_FrontMaterial.ambient
		+ diff  * texture2D(diffuse,  gl_TexCoord[0].st)  * gl_FrontMaterial.diffuse
		+ spec  * texture2D(specular, gl_TexCoord[0].st)
		+ color * texture2D(emit,     gl_TexCoord[0].st);
	*/
	gl_FragColor = gl_FrontLightModelProduct.sceneColor;
}