import typescript from '@rollup/plugin-typescript';
import resolve from '@rollup/plugin-node-resolve';
import commonjs from '@rollup/plugin-commonjs';
import json from '@rollup/plugin-json';
import replace from '@rollup/plugin-replace';

export default {
  input: 'src/index.ts',
  output: [
    { file: 'dist/index.cjs', format: 'cjs', sourcemap: true, exports: 'named', inlineDynamicImports: true },
    { file: 'dist/index.mjs', format: 'esm', sourcemap: true, inlineDynamicImports: true }
  ],
  plugins: [
    resolve({ extensions: ['.mjs', '.js', '.json', '.ts'] }),
    commonjs(),
    json(),
    replace({
      preventAssignment: true,
      __VERSION__: JSON.stringify(process.env.npm_package_version),
    }),
    typescript({ tsconfig: './tsconfig.json', declaration: true, declarationDir: 'dist' })
  ]
};
