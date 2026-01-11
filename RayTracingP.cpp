#include <cstdlib>
#include <cstdio>
#include <cmath>
#include <fstream>
#include <vector>
#include <iostream>
#include <cassert>
#include <algorithm>
#include <random>

#if defined __linux__ || defined __APPLE__
#else
#ifndef M_PI
#define M_PI 3.141592653589793
#endif
#ifndef INFINITY
#define INFINITY 1e8
#endif
#endif

template<typename T>
class Vec3
{
public:
    T x, y, z;

    Vec3() : x(T(0)), y(T(0)), z(T(0)) {}
    Vec3(T xx) : x(xx), y(xx), z(xx) {}
    Vec3(T xx, T yy, T zz) : x(xx), y(yy), z(zz) {}

    Vec3& normalize()
    {
        T nor2 = length2();
        if (nor2 > 0) 
        {
            T invNor = 1 / sqrt(nor2);
            x *= invNor, y *= invNor, z *= invNor;
        }
        return *this;
    }

    Vec3<T> operator * (const T &f) const { return Vec3<T>(x * f, y * f, z * f); }
    Vec3<T> operator * (const Vec3<T> &v) const { return Vec3<T>(x * v.x, y * v.y, z * v.z); }
    T dot(const Vec3<T> &v) const { return x * v.x + y * v.y + z * v.z; }
    Vec3<T> operator - (const Vec3<T> &v) const { return Vec3<T>(x - v.x, y - v.y, z - v.z); }
    Vec3<T> operator + (const Vec3<T> &v) const { return Vec3<T>(x + v.x, y + v.y, z + v.z); }
    Vec3<T>& operator += (const Vec3<T> &v) { x += v.x, y += v.y, z += v.z; return *this; }
    Vec3<T>& operator *= (const Vec3<T> &v) { x *= v.x, y *= v.y, z *= v.z; return *this; }
    Vec3<T> operator - () const { return Vec3<T>(-x, -y, -z); }
    T length2() const { return x * x + y * y + z * z; }
    T length() const { return sqrt(length2()); }

    friend std::ostream & operator << (std::ostream &os, const Vec3<T> &v)
    {
        os << "[" << v.x << " " << v.y << " " << v.z << "]";
        return os;
    }
};

typedef Vec3<float> Vec3f;

class Cube
{
public:
    Vec3f minBounds, maxBounds;
    Vec3f surfaceColor, emissionColor;
    float transparency, reflection;

    Cube(
        const Vec3f &c,
        const float &s,
        const Vec3f &sc,
        const float &refl = 0,
        const float &transp = 0,
        const Vec3f &ec = 0) :
        surfaceColor(sc), emissionColor(ec),
        transparency(transp), reflection(refl)
    {
        minBounds = c - Vec3f(s);
        maxBounds = c + Vec3f(s);
    }

    bool intersect(const Vec3f &rayorig, const Vec3f &raydir, float &t0, float &t1) const
    {
        float tmin = (minBounds.x - rayorig.x) / raydir.x;
        float tmax = (maxBounds.x - rayorig.x) / raydir.x;
        if (tmin > tmax) std::swap(tmin, tmax);

        float tymin = (minBounds.y - rayorig.y) / raydir.y;
        float tymax = (maxBounds.y - rayorig.y) / raydir.y;
        if (tymin > tymax) std::swap(tymin, tymax);

        if ((tmin > tymax) || (tymin > tmax)) return false;

        if (tymin > tmin) tmin = tymin;
        if (tymax < tmax) tmax = tymax;

        float tzmin = (minBounds.z - rayorig.z) / raydir.z;
        float tzmax = (maxBounds.z - rayorig.z) / raydir.z;
        if (tzmin > tzmax) std::swap(tzmin, tzmax);

        if ((tmin > tzmax) || (tzmin > tmax)) return false;

        if (tzmin > tmin) tmin = tzmin;
        if (tzmax < tmax) tmax = tzmax;

        t0 = tmin;
        t1 = tmax;

        return tmax > 0;
    }

    Vec3f getNormal(const Vec3f& phit) const 
    {
        float epsilon = 0.001f;
        if (std::abs(phit.x - minBounds.x) < epsilon) return Vec3f(-1, 0, 0);
        if (std::abs(phit.x - maxBounds.x) < epsilon) return Vec3f(1, 0, 0);
        if (std::abs(phit.y - minBounds.y) < epsilon) return Vec3f(0, -1, 0);
        if (std::abs(phit.y - maxBounds.y) < epsilon) return Vec3f(0, 1, 0);
        if (std::abs(phit.z - minBounds.z) < epsilon) return Vec3f(0, 0, -1);
        if (std::abs(phit.z - maxBounds.z) < epsilon) return Vec3f(0, 0, 1);
        return Vec3f(0, 1, 0);
    }
};

#define MAX_RAY_DEPTH 5

float mix(const float &a, const float &b, const float &mixValue)
{
    return b * mixValue + a * (1.0f - mixValue);
}

Vec3f trace(
    const Vec3f &rayorig,
    const Vec3f &raydir,
    const std::vector<Cube> &cubes,
    const int &depth)
{
    float tnear = INFINITY;
    const Cube* cube = NULL;

    for (int i = 0; i < cubes.size(); ++i) 
    {
        float t0 = INFINITY, t1 = INFINITY;
        if (cubes[i].intersect(rayorig, raydir, t0, t1)) 
        {
            if (t0 < 0) t0 = t1;
            if (t0 < tnear) 
            {
                tnear = t0;
                cube = &cubes[i];
            }
        }
    }

    if (!cube) return Vec3f(2);

    Vec3f surfaceColor = 0;
    Vec3f phit = rayorig + raydir * tnear;
    Vec3f nhit = cube->getNormal(phit);
    float bias = 1e-4;
    bool inside = false;

    if (raydir.dot(nhit) > 0) 
    {
        nhit = -nhit;
        inside = true;
    }

    if ((cube->transparency > 0 || cube->reflection > 0) && depth < MAX_RAY_DEPTH) 
    {
        float facingratio = -raydir.dot(nhit);
        float fresneleffect = mix(pow(1 - facingratio, 3), 1, 0.1);
        Vec3f refldir = raydir - nhit * 2 * raydir.dot(nhit);
        refldir.normalize();

        Vec3f reflection = trace(phit + nhit * bias, refldir, cubes, depth + 1);
        Vec3f refraction = 0;

        if (cube->transparency) 
        {
            float ior = 1.1, eta = (inside) ? ior : 1 / ior;
            float cosi = -nhit.dot(raydir);
            float k = 1 - eta * eta * (1 - cosi * cosi);
            Vec3f refrdir = raydir * eta + nhit * (eta * cosi - sqrt(k));
            refrdir.normalize();
            refraction = trace(phit - nhit * bias, refrdir, cubes, depth + 1);
        }

        surfaceColor = (
            reflection * fresneleffect +
            refraction * (1 - fresneleffect) * cube->transparency) * cube->surfaceColor;
    }
    else 
    {
        for (int i = 0; i < cubes.size(); ++i) 
        {
            if (cubes[i].emissionColor.x > 0) 
            {
                Vec3f transmission = 1;
                Vec3f lightDirection = ((cubes[i].minBounds + cubes[i].maxBounds) * 0.5f) - phit;
                lightDirection.normalize();

                for (int j = 0; j < cubes.size(); ++j) 
                {
                    if (i != j) 
                    {
                        float t0, t1;
                        if (cubes[j].intersect(phit + nhit * bias, lightDirection, t0, t1)) 
                        {
                            transmission = 0;
                            break;
                        }
                    }
                }
                surfaceColor += cube->surfaceColor * transmission *
                                std::max(float(0), nhit.dot(lightDirection)) * cubes[i].emissionColor;
            }
        }
    }

    return surfaceColor + cube->emissionColor;
}

void render(const std::vector<Cube> &cubes)
{
    int width = 640;
    int height = 480;
    Vec3f *image = new Vec3f[width * height], *pixel = image;
    float invWidth = 1 / float(width), invHeight = 1 / float(height);
    float fov = 30, aspectratio = width / float(height);
    float angle = tan(M_PI * 0.5 * fov / 180.);

    for (int y = 0; y < height; ++y) 
    {
        for (int x = 0; x < width; ++x, ++pixel) 
        {
            float xx = (2 * ((x + 0.5) * invWidth) - 1) * angle * aspectratio;
            float yy = (1 - 2 * ((y + 0.5) * invHeight)) * angle;
            Vec3f raydir(xx, yy, -1);
            raydir.normalize();
            *pixel = trace(Vec3f(0), raydir, cubes, 0);
        }
    }

    std::ofstream ofs("./output.ppm", std::ios::out | std::ios::binary);
    ofs << "P6\n" << width << " " << height << "\n255\n";

    for (int i = 0; i < width * height; ++i) 
    {
        ofs << (char)(std::min(float(1), image[i].x) * 255) <<
               (char)(std::min(float(1), image[i].y) * 255) <<
               (char)(std::min(float(1), image[i].z) * 255);
    }

    ofs.close();
    delete [] image;
}

int main(int argc, char **argv)
{
    std::vector<Cube> cubes;

    // Floor
    cubes.push_back(Cube(Vec3f(0.0, -24, -20), 20.0f, Vec3f(0.20), 0, 0.0));
    
    // Geometry
    cubes.push_back(Cube(Vec3f(0.0, 0, -20), 4.0f, Vec3f(1.00, 0.32, 0.36), 1, 0.5));
    cubes.push_back(Cube(Vec3f(5.0, -1, -15), 2.0f, Vec3f(0.90, 0.76, 0.46), 1, 0.0));
    cubes.push_back(Cube(Vec3f(5.0, 0, -25), 3.0f, Vec3f(0.65, 0.77, 0.97), 1, 0.0));
    cubes.push_back(Cube(Vec3f(-5.5, 0, -15), 3.0f, Vec3f(0.90, 0.90, 0.90), 1, 0.0));
    
    // Light
    cubes.push_back(Cube(Vec3f(0.0, 20, -30), 3.0f, Vec3f(0.00), 0, 0.0, Vec3f(3)));

    render(cubes);

    return 0;
}