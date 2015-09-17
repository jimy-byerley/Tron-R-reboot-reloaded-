varying vec3 N;
varying vec3 v;
varying vec4 vertex;

void main(void)
{
	vertex = gl_Vertex;
	v = vec3(gl_ModelViewMatrix * gl_Vertex);  // vertex position in eye coordinates
	N = normalize(gl_NormalMatrix * gl_Normal); // normal in eye coordinates
	gl_TexCoord[0] = gl_MultiTexCoord0;
	gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
}