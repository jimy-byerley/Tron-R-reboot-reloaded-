attribute vec4 Tangent;
varying vec3 T, B, N;


void main()
{
	vec3 pos = vec3(gl_Vertex);

	T   = Tangent.xyz;
	B   = cross(gl_Normal, Tangent.xyz);
	N   = gl_Normal;

	gl_TexCoord[1] = ftransform();
    gl_TexCoord[2].xyz = pos - gl_ModelViewMatrixInverse[3].xyz;
    gl_TexCoord[0] = gl_MultiTexCoord0*0.5+0.5;
    gl_Position = ftransform();
}