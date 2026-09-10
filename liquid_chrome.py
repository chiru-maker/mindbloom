"""
liquid_chrome.py
----------------
Streamlit component integration for React Bits <LiquidChrome />.

Renders an interactive, GPU-accelerated LiquidChrome WebGL canvas with
mouse/touch ripple distortion physics and customizable base colors,
speed, amplitude, and frequency parameters.
"""

import json
import streamlit as st
import streamlit.components.v1 as components


def get_liquid_chrome_html(
    base_color=[0.1, 0.1, 0.1],
    speed=0.2,
    amplitude=0.3,
    frequency_x=3.0,
    frequency_y=3.0,
    interactive=True,
    overlay_html="",
    border_radius="16px",
):
    """
    Generates the standalone HTML/JS with ogl and native WebGL fallback
    implementing the exact React Bits LiquidChrome shaders and interaction.
    """
    base_color_json = json.dumps(base_color)
    interactive_json = "true" if interactive else "false"

    html_code = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Liquid Chrome</title>
  <style>
    * {{
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }}
    html, body {{
      width: 100%;
      height: 100%;
      overflow: hidden;
      background: transparent;
    }}
    .liquidChrome-container {{
      width: 100%;
      height: 100%;
      position: relative;
      border-radius: {border_radius};
      overflow: hidden;
      display: flex;
      align-items: center;
      justify-content: center;
      background: #090d16;
      box-shadow: 0 12px 36px rgba(0, 0, 0, 0.45);
      border: 1px solid rgba(255, 255, 255, 0.08);
    }}
    canvas {{
      position: absolute;
      top: 0;
      left: 0;
      width: 100% !important;
      height: 100% !important;
      display: block;
      cursor: crosshair;
    }}
    .liquid-overlay {{
      position: relative;
      z-index: 10;
      pointer-events: none;
      width: 100%;
      height: 100%;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 24px;
      text-align: center;
      color: #ffffff;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    }}
  </style>
</head>
<body>
  <div id="liquid-container" class="liquidChrome-container">
    {f'<div class="liquid-overlay">{overlay_html}</div>' if overlay_html else ''}
  </div>

  <script type="module">
    // Primary: Load OGL from high-performance ESM CDN
    import {{ Renderer, Program, Mesh, Triangle }} from 'https://esm.sh/ogl@0.0.116';

    const container = document.getElementById('liquid-container');
    const baseColor = {base_color_json};
    const speed = {speed};
    const amplitude = {amplitude};
    const frequencyX = {frequency_x};
    const frequencyY = {frequency_y};
    const interactive = {interactive_json};

    try {{
      const renderer = new Renderer({{ antialias: true, alpha: true }});
      const gl = renderer.gl;
      gl.clearColor(0.05, 0.08, 0.12, 1.0);

      const vertexShader = `
        attribute vec2 position;
        attribute vec2 uv;
        varying vec2 vUv;
        void main() {{
          vUv = uv;
          gl_Position = vec4(position, 0.0, 1.0);
        }}
      `;

      const fragmentShader = `
        precision highp float;
        uniform float uTime;
        uniform vec3 uResolution;
        uniform vec3 uBaseColor;
        uniform float uAmplitude;
        uniform float uFrequencyX;
        uniform float uFrequencyY;
        uniform vec2 uMouse;
        varying vec2 vUv;

        vec4 renderImage(vec2 uvCoord) {{
            vec2 fragCoord = uvCoord * uResolution.xy;
            vec2 uv = (2.0 * fragCoord - uResolution.xy) / min(uResolution.x, uResolution.y);

            for (float i = 1.0; i < 10.0; i++){{
                uv.x += uAmplitude / i * cos(i * uFrequencyX * uv.y + uTime + uMouse.x * 3.14159);
                uv.y += uAmplitude / i * cos(i * uFrequencyY * uv.x + uTime + uMouse.y * 3.14159);
            }}

            vec2 diff = (uvCoord - uMouse);
            float dist = length(diff);
            float falloff = exp(-dist * 20.0);
            float ripple = sin(10.0 * dist - uTime * 2.0) * 0.03;
            uv += (diff / (dist + 0.0001)) * ripple * falloff;

            vec3 color = uBaseColor / abs(sin(uTime - uv.y - uv.x));
            return vec4(color, 1.0);
        }}

        void main() {{
            vec4 col = vec4(0.0);
            int samples = 0;
            for (int i = -1; i <= 1; i++){{
                for (int j = -1; j <= 1; j++){{
                    vec2 offset = vec2(float(i), float(j)) * (1.0 / min(uResolution.x, uResolution.y));
                    col += renderImage(vUv + offset);
                    samples++;
                }}
            }}
            gl_FragColor = col / float(samples);
        }}
      `;

      const geometry = new Triangle(gl);
      const program = new Program(gl, {{
        vertex: vertexShader,
        fragment: fragmentShader,
        uniforms: {{
          uTime: {{ value: 0 }},
          uResolution: {{
            value: new Float32Array([container.clientWidth || window.innerWidth, container.clientHeight || window.innerHeight, 1.0])
          }},
          uBaseColor: {{ value: new Float32Array(baseColor) }},
          uAmplitude: {{ value: amplitude }},
          uFrequencyX: {{ value: frequencyX }},
          uFrequencyY: {{ value: frequencyY }},
          uMouse: {{ value: new Float32Array([0.5, 0.5]) }}
        }}
      }});
      const mesh = new Mesh(gl, {{ geometry, program }});

      function resize() {{
        const w = container.clientWidth || window.innerWidth;
        const h = container.clientHeight || window.innerHeight;
        renderer.setSize(w, h);
        const resUniform = program.uniforms.uResolution.value;
        resUniform[0] = gl.canvas.width;
        resUniform[1] = gl.canvas.height;
        resUniform[2] = gl.canvas.width / (gl.canvas.height || 1.0);
      }}
      window.addEventListener('resize', resize);
      resize();

      function handleMouseMove(event) {{
        const rect = container.getBoundingClientRect();
        const x = (event.clientX - rect.left) / rect.width;
        const y = 1 - (event.clientY - rect.top) / rect.height;
        const mouseUniform = program.uniforms.uMouse.value;
        mouseUniform[0] = x;
        mouseUniform[1] = y;
      }}

      function handleTouchMove(event) {{
        if (event.touches.length > 0) {{
          const touch = event.touches[0];
          const rect = container.getBoundingClientRect();
          const x = (touch.clientX - rect.left) / rect.width;
          const y = 1 - (touch.clientY - rect.top) / rect.height;
          const mouseUniform = program.uniforms.uMouse.value;
          mouseUniform[0] = x;
          mouseUniform[1] = y;
        }}
      }}

      if (interactive) {{
        container.addEventListener('mousemove', handleMouseMove);
        container.addEventListener('touchmove', handleTouchMove, {{ passive: true }});
      }}

      let animationId;
      function update(t) {{
        animationId = requestAnimationFrame(update);
        program.uniforms.uTime.value = t * 0.001 * speed;
        renderer.render({{ scene: mesh }});
      }}
      animationId = requestAnimationFrame(update);

      container.appendChild(gl.canvas);
    }} catch (e) {{
      console.warn("OGL initialization fallback:", e);
      initVanillaWebGL();
    }}

    function initVanillaWebGL() {{
      const canvas = document.createElement('canvas');
      container.appendChild(canvas);
      const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
      if (!gl) return;

      function createShader(type, source) {{
        const s = gl.createShader(type);
        gl.shaderSource(s, source);
        gl.compileShader(s);
        return s;
      }}

      const vs = createShader(gl.VERTEX_SHADER, `
        attribute vec2 position;
        varying vec2 vUv;
        void main() {{
          vUv = position * 0.5 + 0.5;
          gl_Position = vec4(position, 0.0, 1.0);
        }}
      `);

      const fsSource = `
        precision highp float;
        uniform float uTime;
        uniform vec3 uResolution;
        uniform vec3 uBaseColor;
        uniform float uAmplitude;
        uniform float uFrequencyX;
        uniform float uFrequencyY;
        uniform vec2 uMouse;
        varying vec2 vUv;

        vec4 renderImage(vec2 uvCoord) {{
            vec2 fragCoord = uvCoord * uResolution.xy;
            vec2 uv = (2.0 * fragCoord - uResolution.xy) / min(uResolution.x, uResolution.y);

            for (float i = 1.0; i < 10.0; i++){{
                uv.x += uAmplitude / i * cos(i * uFrequencyX * uv.y + uTime + uMouse.x * 3.14159);
                uv.y += uAmplitude / i * cos(i * uFrequencyY * uv.x + uTime + uMouse.y * 3.14159);
            }}

            vec2 diff = (uvCoord - uMouse);
            float dist = length(diff);
            float falloff = exp(-dist * 20.0);
            float ripple = sin(10.0 * dist - uTime * 2.0) * 0.03;
            uv += (diff / (dist + 0.0001)) * ripple * falloff;

            vec3 color = uBaseColor / abs(sin(uTime - uv.y - uv.x));
            return vec4(color, 1.0);
        }}

        void main() {{
            vec4 col = vec4(0.0);
            int samples = 0;
            for (int i = -1; i <= 1; i++){{
                for (int j = -1; j <= 1; j++){{
                    vec2 offset = vec2(float(i), float(j)) * (1.0 / min(uResolution.x, uResolution.y));
                    col += renderImage(vUv + offset);
                    samples++;
                }}
            }}
            gl_FragColor = col / float(samples);
        }}
      `;
      const fs = createShader(gl.FRAGMENT_SHADER, fsSource);
      const prg = gl.createProgram();
      gl.attachShader(prg, vs);
      gl.attachShader(prg, fs);
      gl.linkProgram(prg);
      gl.useProgram(prg);

      const buf = gl.createBuffer();
      gl.bindBuffer(gl.ARRAY_BUFFER, buf);
      gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([
        -1, -1,  1, -1, -1,  1,
        -1,  1,  1, -1,  1,  1
      ]), gl.STATIC_DRAW);

      const posLoc = gl.getAttribLocation(prg, "position");
      gl.enableVertexAttribArray(posLoc);
      gl.vertexAttribPointer(posLoc, 2, gl.FLOAT, false, 0, 0);

      const uTime = gl.getUniformLocation(prg, "uTime");
      const uRes = gl.getUniformLocation(prg, "uResolution");
      const uCol = gl.getUniformLocation(prg, "uBaseColor");
      const uAmp = gl.getUniformLocation(prg, "uAmplitude");
      const uFreqX = gl.getUniformLocation(prg, "uFrequencyX");
      const uFreqY = gl.getUniformLocation(prg, "uFrequencyY");
      const uMouse = gl.getUniformLocation(prg, "uMouse");

      let mouse = [0.5, 0.5];
      if (interactive) {{
        container.addEventListener('mousemove', (e) => {{
          const rect = container.getBoundingClientRect();
          mouse[0] = (e.clientX - rect.left) / rect.width;
          mouse[1] = 1 - (e.clientY - rect.top) / rect.height;
        }});
      }}

      function resize() {{
        canvas.width = container.clientWidth || window.innerWidth;
        canvas.height = container.clientHeight || window.innerHeight;
        gl.viewport(0, 0, canvas.width, canvas.height);
      }}
      window.addEventListener('resize', resize);
      resize();

      function render(t) {{
        gl.uniform1f(uTime, t * 0.001 * speed);
        gl.uniform3f(uRes, canvas.width, canvas.height, canvas.width / canvas.height);
        gl.uniform3fv(uCol, baseColor);
        gl.uniform1f(uAmp, amplitude);
        gl.uniform1f(uFreqX, frequencyX);
        gl.uniform1f(uFreqY, frequencyY);
        gl.uniform2fv(uMouse, mouse);

        gl.drawArrays(gl.TRIANGLES, 0, 6);
        requestAnimationFrame(render);
      }}
      requestAnimationFrame(render);
    }}
  </script>
</body>
</html>
"""
    return html_code


def render_liquid_chrome(
    base_color=[0.1, 0.1, 0.1],
    speed=0.2,
    amplitude=0.3,
    frequency_x=3.0,
    frequency_y=3.0,
    interactive=True,
    height=420,
    overlay_html="",
    border_radius="16px",
):
    """
    Renders the React Bits LiquidChrome component inside Streamlit.
    """
    html_code = get_liquid_chrome_html(
        base_color=base_color,
        speed=speed,
        amplitude=amplitude,
        frequency_x=frequency_x,
        frequency_y=frequency_y,
        interactive=interactive,
        overlay_html=overlay_html,
        border_radius=border_radius,
    )
    return components.html(html_code, height=height, scrolling=False)
