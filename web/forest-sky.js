import * as THREE from 'three'

// Camera-centred sky: one opaque draw, no texture downloads or cloud sprites.
// Only the cloud coordinates drift; the horizon stays fixed as the player walks.
export function createForestSky(scene) {
  const uniforms = {
    time: { value: 0 },
    zenith: { value: new THREE.Color(0x167ee6) },
    horizon: { value: new THREE.Color(0xa8dafb) },
    sunDirection: { value: new THREE.Vector3(0.4, 0.8, -0.3).normalize() },
  }
  const material = new THREE.ShaderMaterial({
    uniforms, side: THREE.BackSide, depthWrite: false, fog: false,
    vertexShader: `
      varying vec3 skyDirection;
      void main() {
        skyDirection = position;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
      }
    `,
    fragmentShader: `
      uniform float time;
      uniform vec3 zenith, horizon, sunDirection;
      varying vec3 skyDirection;
      float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
      float noise(vec2 p) {
        vec2 i = floor(p), f = fract(p);
        f = f * f * (3.0 - 2.0 * f);
        return mix(mix(hash(i), hash(i + vec2(1, 0)), f.x),
                   mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), f.x), f.y);
      }
      float fbm(vec2 p) {
        float value = 0.0, amplitude = 0.5;
        for (int i = 0; i < 5; i++) {
          value += amplitude * noise(p);
          p = mat2(0.8, -0.6, 0.6, 0.8) * p * 2.03 + 13.7;
          amplitude *= 0.5;
        }
        return value;
      }
      void main() {
        vec3 direction = normalize(skyDirection);
        float elevation = max(direction.y, 0.0);
        vec3 sky = mix(horizon, zenith, pow(elevation, 0.32));
        // High, sparse cumulus with a gently feathered edge and shaded underside.
        vec2 p = direction.xz / (elevation + 0.24) * 2.4;
        p += vec2(time * 0.0025, time * 0.0007) + vec2(4.1, 8.3);
        float density = fbm(p);
        float cloud = smoothstep(0.56, 0.69, density) * smoothstep(0.025, 0.16, elevation);
        vec3 cloudColor = mix(vec3(0.69, 0.78, 0.88), vec3(1.05, 1.04, 1.01), smoothstep(0.58, 0.76, density));
        sky = mix(sky, cloudColor, cloud);
        float alignment = max(dot(direction, normalize(sunDirection)), 0.0);
        sky += vec3(1.0, 0.85, 0.60) * pow(alignment, 90.0) * 0.14 * (1.0 - cloud);
        gl_FragColor = vec4(sky, 1.0);
      }
    `,
  })
  const dome = new THREE.Mesh(new THREE.SphereGeometry(140, 32, 16), material)
  dome.name = 'Forest_Daylight_Sky'
  dome.frustumCulled = false
  dome.renderOrder = -1000
  scene.add(dome)
  return {
    update(dt, camera, sunDirection) {
      uniforms.time.value += dt
      dome.position.copy(camera.position)
      if (sunDirection.lengthSq() > 0) uniforms.sunDirection.value.copy(sunDirection)
    },
  }
}
