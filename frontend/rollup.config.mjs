import resolve from "@rollup/plugin-node-resolve";
import commonjs from "@rollup/plugin-commonjs";
import typescript from "@rollup/plugin-typescript";

const baseTs = {
  tsconfig: "./tsconfig.json",
  declaration: false,
  declarationMap: false,
  sourceMap: true,
};

const baseSharedPlugins = [resolve({ browser: true }), commonjs()];

export default [
  {
    input: "src/qr-card.ts",
    output: {
      file: "../custom_components/whatsapp_bridge/panel-static/whatsapp-qr-card.js",
      format: "es",
      sourcemap: true,
    },
    plugins: [
      ...baseSharedPlugins,
      typescript({
        ...baseTs,
        outDir: "../custom_components/whatsapp_bridge/panel-static",
      }),
    ],
  },
  {
    input: "src/panel.ts",
    output: {
      file: "../custom_components/whatsapp_bridge/panel-static/whatsapp-panel.js",
      format: "es",
      sourcemap: true,
    },
    plugins: [
      ...baseSharedPlugins,
      typescript({
        ...baseTs,
        outDir: "../custom_components/whatsapp_bridge/panel-static",
      }),
    ],
  },
];
