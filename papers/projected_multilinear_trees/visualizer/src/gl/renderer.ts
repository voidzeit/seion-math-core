/**
 * WebGL2 renderer for the extremal landscape.
 *
 * Real GPU rasterisation: the surface is an indexed triangle mesh uploaded
 * once, shaded per-fragment, with depth testing and MSAA. Nothing here decides
 * mathematics -- vertex heights come from `math/pmt_exact`, and the admissible
 * region is passed as a uniform so that changing eta never touches the mesh.
 * That is the point of the instrument: the surface provably does not move.
 */

import { E } from "../math/pmt_exact";

export interface GpuInfo {
  api: "webgl2";
  webgpuAvailable: boolean;
  vendor: string;
  renderer: string;
  maxSamples: number;
  dpr: number;
}

export interface Quality {
  name: "LOW" | "MEDIUM" | "HIGH" | "ULTRA" | "EXTREME" | "INSANE";
  n: number;
}

/**
 * Mesh resolutions. The first four are the brief's ladder; the last two exist
 * because at 512 neither adapter on this machine is remotely loaded — 524k
 * triangles render in ~0.12 ms on the integrated GPU. A quality ladder that
 * tops out below the point where hardware matters cannot tell adapters apart,
 * so it cannot justify choosing one.
 *
 * INSANE builds a 2048x2048 grid: 4.2M vertices, 8.4M triangles, ~100 MB of
 * indices.
 */
export const QUALITIES: Quality[] = [
  { name: "LOW", n: 64 },
  { name: "MEDIUM", n: 128 },
  { name: "HIGH", n: 256 },
  { name: "ULTRA", n: 512 },
  { name: "EXTREME", n: 1024 },
  { name: "INSANE", n: 2048 },
];

/**
 * The surface, in GLSL. This is a second implementation of `math/pmt_exact.E`
 * and therefore a real divergence risk: it runs in float32 on the GPU while the
 * tested implementation runs in float64 on the CPU. `probeSurface()` below
 * exists to compare them, so the duplication is checked rather than trusted.
 */
export const SURF_GLSL = `
float surf(vec2 p){
  float q=p.x, s=p.y;
  float cq=max(0.0,1.0-q*q), cs=max(0.0,1.0-s*s);
  return sqrt(max(0.0, q*q + cq*s*s + 2.0*q*sqrt(cq)*s*sqrt(cs)));
}`;

const VERT = `#version 300 es
precision highp float;
layout(location=0) in vec2 aQS;
uniform mat4 uMVP;
uniform float uEta;
out float vZ;
out float vInside;
out vec3 vN;
${SURF_GLSL}
void main(){
  float z = surf(aQS);
  vZ = z;
  vInside = (aQS.x <= uEta + 1e-6 && aQS.y <= uEta + 1e-6) ? 1.0 : 0.0;
  // analytic-ish normal by central differences on the GPU
  float h = 0.004;
  float zx = surf(aQS + vec2(h,0.0)) - surf(aQS - vec2(h,0.0));
  float zy = surf(aQS + vec2(0.0,h)) - surf(aQS - vec2(0.0,h));
  vN = normalize(vec3(-zx/(2.0*h), -zy/(2.0*h), 1.0));
  gl_Position = uMVP * vec4(aQS.x, aQS.y, z, 1.0);
}`;

const FRAG = `#version 300 es
precision highp float;
in float vZ;
in float vInside;
in vec3 vN;
uniform float uEmax;
uniform int uDark;
out vec4 frag;

vec3 ramp(float t){
  t = clamp(t,0.0,1.0);
  vec3 c1 = vec3(0.055,0.231,0.271);   // deep teal
  vec3 c2 = vec3(0.369,0.549,0.478);   // sage
  vec3 c3 = vec3(0.847,0.753,0.541);   // sand
  return t<0.5 ? mix(c1,c2,t*2.0) : mix(c2,c3,(t-0.5)*2.0);
}

void main(){
  vec3 base = ramp(vZ/uEmax);
  vec3 L = normalize(vec3(0.42,-0.55,0.72));
  float lam = 0.55 + 0.45*max(0.0, dot(normalize(vN), L));
  vec3 col = base*lam;
  // Unreachable terrain is desaturated toward the ground, not made
  // translucent: alpha blending against a depth-tested mesh is order
  // dependent, and an unsorted transparent surface renders incorrectly.
  if (vInside < 0.5){
    vec3 ground = vec3(uDark==1 ? 0.075 : 0.945);
    float grey = dot(col, vec3(0.299,0.587,0.114));
    col = mix(mix(vec3(grey), ground, 0.55), col, 0.22);
  }
  frag = vec4(col, 1.0);
}`;

const LINE_VERT = `#version 300 es
precision highp float;
layout(location=0) in vec3 aPos;
uniform mat4 uMVP;
void main(){ gl_Position = uMVP * vec4(aPos,1.0); }`;

const LINE_FRAG = `#version 300 es
precision highp float;
uniform vec4 uColor;
out vec4 frag;
void main(){ frag = uColor; }`;

/** Vertex program used only to read the shader's own surface back to the CPU. */
const PROBE_VERT = `#version 300 es
precision highp float;
layout(location=0) in vec2 aQS;
out float vProbe;
${SURF_GLSL}
void main(){ vProbe = surf(aQS); gl_Position = vec4(0.0,0.0,0.0,1.0); }`;

const PROBE_FRAG = `#version 300 es
precision highp float;
out vec4 frag;
void main(){ frag = vec4(0.0); }`;

function compile(
  gl: WebGL2RenderingContext, vs: string, fs: string, feedback?: string[],
): WebGLProgram {
  const mk = (type: number, src: string) => {
    const s = gl.createShader(type)!;
    gl.shaderSource(s, src);
    gl.compileShader(s);
    if (!gl.getShaderParameter(s, gl.COMPILE_STATUS))
      throw new Error("shader: " + gl.getShaderInfoLog(s));
    return s;
  };
  const p = gl.createProgram()!;
  gl.attachShader(p, mk(gl.VERTEX_SHADER, vs));
  gl.attachShader(p, mk(gl.FRAGMENT_SHADER, fs));
  if (feedback) gl.transformFeedbackVaryings(p, feedback, gl.SEPARATE_ATTRIBS);
  gl.linkProgram(p);
  if (!gl.getProgramParameter(p, gl.LINK_STATUS))
    throw new Error("link: " + gl.getProgramInfoLog(p));
  return p;
}

/* ------------------------------------------------------------ matrices */
type M4 = Float32Array;
const ident = (): M4 => new Float32Array([1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1]);
function mul(a: M4, b: M4): M4 {
  const o = new Float32Array(16);
  for (let i = 0; i < 4; i++)
    for (let j = 0; j < 4; j++) {
      let v = 0;
      for (let k = 0; k < 4; k++) v += a[k * 4 + j] * b[i * 4 + k];
      o[i * 4 + j] = v;
    }
  return o;
}
function perspective(fovy: number, aspect: number, near: number, far: number): M4 {
  const f = 1 / Math.tan(fovy / 2), o = new Float32Array(16);
  o[0] = f / aspect; o[5] = f; o[11] = -1;
  o[10] = (far + near) / (near - far); o[14] = (2 * far * near) / (near - far);
  return o;
}
function lookAt(eye: number[], c: number[], up: number[]): M4 {
  const z = norm([eye[0]-c[0], eye[1]-c[1], eye[2]-c[2]]);
  const x = norm(cross(up, z)), y = cross(z, x);
  const o = ident();
  o[0]=x[0]; o[4]=x[1]; o[8]=x[2];  o[12]=-dot(x,eye);
  o[1]=y[0]; o[5]=y[1]; o[9]=y[2];  o[13]=-dot(y,eye);
  o[2]=z[0]; o[6]=z[1]; o[10]=z[2]; o[14]=-dot(z,eye);
  return o;
}
const cross=(a:number[],b:number[])=>[a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]];
const dot=(a:number[],b:number[])=>a[0]*b[0]+a[1]*b[1]+a[2]*b[2];
const norm=(a:number[])=>{const l=Math.hypot(a[0],a[1],a[2])||1;return [a[0]/l,a[1]/l,a[2]/l];};

export interface CameraState { az: number; el: number; dist: number; }

export class Observatory {
  private gl: WebGL2RenderingContext;
  private progSurf: WebGLProgram;
  private progLine: WebGLProgram;
  private progProbe: WebGLProgram;
  private vaoSurf!: WebGLVertexArrayObject;
  private idxCount = 0;
  private lineBuf: WebGLBuffer;
  private vaoLine: WebGLVertexArrayObject;
  readonly info: GpuInfo;
  quality: Quality;
  cam: CameraState = { az: -0.86, el: 0.52, dist: 3.1 };
  triangles = 0;

  constructor(private canvas: HTMLCanvasElement, quality: Quality) {
    const gl = canvas.getContext("webgl2", {
      antialias: true, depth: true, alpha: false, powerPreference: "high-performance",
    });
    if (!gl) throw new Error("WEBGL2_UNAVAILABLE");
    this.gl = gl;
    this.quality = quality;
    this.progSurf = compile(gl, VERT, FRAG);
    this.progLine = compile(gl, LINE_VERT, LINE_FRAG);

    const dbg = gl.getExtension("WEBGL_debug_renderer_info");
    this.info = {
      api: "webgl2",
      webgpuAvailable: typeof navigator !== "undefined" && "gpu" in navigator,
      vendor: dbg ? String(gl.getParameter(dbg.UNMASKED_VENDOR_WEBGL)) : "hidden",
      renderer: dbg ? String(gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL)) : "hidden",
      maxSamples: gl.getParameter(gl.MAX_SAMPLES) as number,
      dpr: window.devicePixelRatio || 1,
    };

    this.lineBuf = gl.createBuffer()!;
    this.vaoLine = gl.createVertexArray()!;
    gl.bindVertexArray(this.vaoLine);
    gl.bindBuffer(gl.ARRAY_BUFFER, this.lineBuf);
    gl.enableVertexAttribArray(0);
    gl.vertexAttribPointer(0, 3, gl.FLOAT, false, 0, 0);
    gl.bindVertexArray(null);

    this.progProbe = compile(gl, PROBE_VERT, PROBE_FRAG, ["vProbe"]);
    this.buildSurface();
    gl.enable(gl.DEPTH_TEST);
    // No blending: every fragment is opaque, so nothing depends on draw order.
    gl.disable(gl.BLEND);
  }

  /**
   * Run the *shader's* surface over probe points and read the results back.
   *
   * The GLSL `surf()` is a second implementation of `math/pmt_exact.E`, in
   * float32 rather than float64. Without this, a divergence between the drawn
   * surface and the tested mathematics would be invisible — the picture would
   * simply be wrong in a way no math test could catch.
   */
  probeSurface(points: Float32Array): Float32Array {
    const gl = this.gl, n = points.length / 2;
    const inBuf = gl.createBuffer()!;
    gl.bindBuffer(gl.ARRAY_BUFFER, inBuf);
    gl.bufferData(gl.ARRAY_BUFFER, points, gl.STATIC_DRAW);
    const vao = gl.createVertexArray()!;
    gl.bindVertexArray(vao);
    gl.enableVertexAttribArray(0);
    gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0);

    const outBuf = gl.createBuffer()!;
    gl.bindBuffer(gl.ARRAY_BUFFER, outBuf);
    gl.bufferData(gl.ARRAY_BUFFER, n * 4, gl.STATIC_READ);
    // A buffer may not be bound to ARRAY_BUFFER and TRANSFORM_FEEDBACK_BUFFER
    // at the same time; leaving it bound here makes the capture silently write
    // nothing, which is exactly how this was first caught.
    gl.bindBuffer(gl.ARRAY_BUFFER, null);

    const tf = gl.createTransformFeedback()!;
    gl.bindTransformFeedback(gl.TRANSFORM_FEEDBACK, tf);
    gl.bindBufferBase(gl.TRANSFORM_FEEDBACK_BUFFER, 0, outBuf);

    gl.useProgram(this.progProbe);
    gl.enable(gl.RASTERIZER_DISCARD);
    gl.beginTransformFeedback(gl.POINTS);
    gl.drawArrays(gl.POINTS, 0, n);
    gl.endTransformFeedback();
    gl.disable(gl.RASTERIZER_DISCARD);

    // Release the transform-feedback bindings before reading the buffer back.
    gl.bindBufferBase(gl.TRANSFORM_FEEDBACK_BUFFER, 0, null);
    gl.bindTransformFeedback(gl.TRANSFORM_FEEDBACK, null);

    const out = new Float32Array(n);
    gl.bindBuffer(gl.ARRAY_BUFFER, outBuf);
    gl.getBufferSubData(gl.ARRAY_BUFFER, 0, out);
    gl.bindBuffer(gl.ARRAY_BUFFER, null);
    gl.bindVertexArray(null);
    gl.deleteBuffer(inBuf); gl.deleteBuffer(outBuf);
    gl.deleteVertexArray(vao); gl.deleteTransformFeedback(tf);
    return out;
  }

  /** The mesh is built once per quality level and never rebuilt for eta. */
  buildSurface(): void {
    const gl = this.gl, n = this.quality.n;
    const verts = new Float32Array((n + 1) * (n + 1) * 2);
    let p = 0;
    for (let i = 0; i <= n; i++)
      for (let j = 0; j <= n; j++) { verts[p++] = i / n; verts[p++] = j / n; }
    const idx = new Uint32Array(n * n * 6);
    let k = 0;
    for (let i = 0; i < n; i++)
      for (let j = 0; j < n; j++) {
        const a = i * (n + 1) + j, b = a + 1, c = a + (n + 1), d = c + 1;
        idx[k++] = a; idx[k++] = c; idx[k++] = b;
        idx[k++] = b; idx[k++] = c; idx[k++] = d;
      }
    this.idxCount = idx.length;
    this.triangles = idx.length / 3;
    if (this.vaoSurf) gl.deleteVertexArray(this.vaoSurf);
    this.vaoSurf = gl.createVertexArray()!;
    gl.bindVertexArray(this.vaoSurf);
    const vb = gl.createBuffer()!;
    gl.bindBuffer(gl.ARRAY_BUFFER, vb);
    gl.bufferData(gl.ARRAY_BUFFER, verts, gl.STATIC_DRAW);
    gl.enableVertexAttribArray(0);
    gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0);
    const ib = gl.createBuffer()!;
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, ib);
    gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, idx, gl.STATIC_DRAW);
    gl.bindVertexArray(null);
  }

  setQuality(q: Quality): void { this.quality = q; this.buildSurface(); }


  private mvp(w: number, h: number): M4 {
    const { az, el, dist } = this.cam;
    const eye = [
      0.5 + dist * Math.cos(el) * Math.sin(az),
      0.5 + dist * Math.cos(el) * Math.cos(az),
      0.55 + dist * Math.sin(el),
    ];
    return mul(perspective(0.62, w / h, 0.05, 40), lookAt(eye, [0.5, 0.5, 0.42], [0, 0, 1]));
  }

  render(eta: number, opts: { diagonal: boolean; square: boolean; peak: boolean;
                              dark: boolean; emax: number; critical: [number,number,number,number];
                              axis: boolean }): void {
    const gl = this.gl, dpr = Math.min(window.devicePixelRatio || 1, 2);
    const w = this.canvas.clientWidth, h = this.canvas.clientHeight;
    this.canvas.width = Math.max(1, w * dpr); this.canvas.height = Math.max(1, h * dpr);
    gl.viewport(0, 0, this.canvas.width, this.canvas.height);
    const bg = opts.dark ? [0.055, 0.078, 0.086, 1] : [0.957, 0.965, 0.961, 1];
    gl.clearColor(bg[0], bg[1], bg[2], bg[3]);
    gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);

    const mvp = this.mvp(w, h);

    gl.useProgram(this.progSurf);
    gl.uniformMatrix4fv(gl.getUniformLocation(this.progSurf, "uMVP"), false, mvp);
    gl.uniform1f(gl.getUniformLocation(this.progSurf, "uEta"), eta);
    gl.uniform1f(gl.getUniformLocation(this.progSurf, "uEmax"), opts.emax);
    gl.uniform1i(gl.getUniformLocation(this.progSurf, "uDark"), opts.dark ? 1 : 0);
    gl.bindVertexArray(this.vaoSurf);
    gl.drawElements(gl.TRIANGLES, this.idxCount, gl.UNSIGNED_INT, 0);

    gl.useProgram(this.progLine);
    gl.uniformMatrix4fv(gl.getUniformLocation(this.progLine, "uMVP"), false, mvp);
    const drawLines = (pts: number[], color: number[]) => {
      gl.uniform4fv(gl.getUniformLocation(this.progLine, "uColor"), color);
      gl.bindVertexArray(this.vaoLine);
      gl.bindBuffer(gl.ARRAY_BUFFER, this.lineBuf);
      gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(pts), gl.DYNAMIC_DRAW);
      gl.drawArrays(gl.LINE_STRIP, 0, pts.length / 3);
    };

    if (opts.axis) {
      const c: number[] = opts.dark ? [0.42, 0.49, 0.51, 1] : [0.35, 0.42, 0.42, 1];
      drawLines([0,0,0, 1,0,0], c); drawLines([0,0,0, 0,1,0], c); drawLines([0,0,0, 0,0,1.25], c);
    }
    if (opts.square) {
      const e = eta, y = 0.0005;
      drawLines([0,0,y, e,0,y, e,e,y, 0,e,y, 0,0,y], opts.critical);
    }
    if (opts.diagonal) {
      const pts: number[] = [];
      for (let i = 0; i <= 240; i++) { const t = i / 240; pts.push(t, t, E(t, t) + 0.004); }
      drawLines(pts, opts.critical);
    }
    if (opts.peak) {
      const t = Math.min(eta, Math.sqrt(2 / 3)), z = E(t, t);
      const r = 0.028, pts: number[] = [];
      for (let i = 0; i <= 48; i++) {
        const a = (i / 48) * Math.PI * 2;
        pts.push(t + r * Math.cos(a), t + r * Math.sin(a), z + 0.006);
      }
      drawLines(pts, opts.critical);
      drawLines([t, t, z, t, t, z + 0.22], opts.critical);
    }
    gl.bindVertexArray(null);
  }
}
