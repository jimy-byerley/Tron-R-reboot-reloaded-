uniform sampler2D bgl_RenderedTexture;
uniform float bloom_fac;

vec4 contrast( in vec4 value )
{
	float fac = 1.;
	//float med = (value.x+value.y+value.z)/3;
	//vec4 result = (value - vec4(med)*0.8)*3;
	
	float m = max(max(value.x, value.y), value.z);
	value.x -= (m-value.x)*fac;
	value.y -= (m-value.y)*fac;
	value.z -= (m-value.z)*fac;
	
	return value;
}

/*
vec4 max( in vec4 a, in vec4 b)
{
	vec4 r = vec4(0);
	r.x = (a.x>b.x)?a.x:b.x;
	r.y = (a.y>b.y)?a.y:b.y;
	r.z = (a.z>b.z)?a.z:b.z;
	return r;
}
*/

/*
#define BRUSH_LEN 75
const vec2 brush [BRUSH_LEN] = {
	vec2( 0,-5), vec2( 0,-4), vec2( 0,-3), vec2( 0,-2), vec2( 0,-1), vec2( 0,0), vec2( 0,1), vec2( 0,2), vec2( 0,3), vec2( 0,4), vec2( 0,5), 
	vec2( 1,-4), vec2( 1,-3), vec2( 1,-2), vec2( 1,-1), vec2( 1,0), vec2( 1,1), vec2( 1,2), vec2( 1,3), vec2( 1,4), 
	vec2( 2,-4), vec2( 2,-3), vec2( 2,-2), vec2( 2,-1), vec2( 2,0), vec2( 2,1), vec2( 2,2), vec2( 2,3), vec2( 2,4), 
	vec2( 3,-4), vec2( 3,-3), vec2( 3,-2), vec2( 3,-1), vec2( 3,0), vec2( 3,1), vec2( 3,2), vec2( 3,3), vec2( 3,4), 
	vec2( 4,-2), vec2( 4,-1), vec2( 4,0), vec2( 4,1), vec2( 4,2), 
	vec2(-4,-2), vec2(-4,-1), vec2(-4,0), vec2(-4,1), vec2(-4,2), 
	vec2(-3,-4), vec2(-3,-3), vec2(-3,-2), vec2(-3,-1), vec2(-3,0), vec2(-3,1), vec2(-3,2), vec2(-3,3), vec2(-3,4), 
	vec2(-2,-4), vec2(-2,-3), vec2(-2,-2), vec2(-2,-1), vec2(-2,0), vec2(-2,1), vec2(-2,2), vec2(-2,3), vec2(-2,4), 
	vec2(-1,-4), vec2(-1,-3), vec2(-1,-2), vec2(-1,-1), vec2(-1,0), vec2(-1,1), vec2(-1,2), vec2(-1,3), vec2(-1,4), 
};
*/

#define BRUSH_LEN 27
const vec2 brush [BRUSH_LEN] = {
vec2( 0,-3), vec2( 0,-2), vec2( 0,-1), vec2( 0,0), vec2( 0,1), vec2( 0,2), vec2( 0,3), 
vec2( 1,-2), vec2( 1,-1), vec2( 1,0), vec2( 1,1), vec2( 1,2), 
vec2( 2,-2), vec2( 2,-1), vec2( 2,0), vec2( 2,1), vec2( 2,2), 
vec2(-2,-2), vec2(-2,-1), vec2(-2,0), vec2(-2,1), vec2(-2,2), 
vec2(-1,-2), vec2(-1,-1), vec2(-1,0), vec2(-1,1), vec2(-1,2), 
};


void main(void)
{

	vec4 bloom = vec4(0);
		
	int j;
	int i;

	for(i=0; i<BRUSH_LEN; i++)
	{
		bloom += texture2D(bgl_RenderedTexture, gl_TexCoord[0].st + brush[i]*bloom_fac); // bloom_fac or 0.0016
	}
	bloom *= 0.8/float(BRUSH_LEN);
	vec4 value =  texture2D(bgl_RenderedTexture, gl_TexCoord[0].st);
	
	gl_FragColor = max(value, contrast(bloom));

}

/*
size = 5
from math import *

t = '{\n'
n = 0
for x in range(0, size):
	c = int(sin(acos(x/size))*size)
	for y in range(-c, c+1):
		t += 'vec2( '+str(x)+','+str(y)+'), '
		n += 1
	t += '\n'


for x in range(-size+1, 0):
	c = int(sin(acos(-x/size))*size)
	for y in range(-c, c+1):
		t += 'vec2('+str(x)+','+str(y)+'), '
		n += 1
	t += '\n'


t += '}\n'

print(t)
print(n)
*/