import fs from 'fs';
import path from 'path';
import { execSync } from 'child_process';
import { fileURLToPath } from 'url';
import crypto from 'crypto';

// 获取 __dirname 等效值
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// 确保目标目录存在
const templatesDir = path.resolve(__dirname, '../app/templates');
const assetsDir = path.resolve(templatesDir, 'assets');

// 清空目标目录
console.log('清空目标目录...');
if (fs.existsSync(assetsDir)) {
  // 删除assets目录中的所有文件
  const files = fs.readdirSync(assetsDir);
  for (const file of files) {
    const filePath = path.join(assetsDir, file);
    if (fs.lstatSync(filePath).isDirectory()) {
      // 如果是目录，递归删除
      fs.rmSync(filePath, { recursive: true, force: true });
    } else {
      // 如果是文件，直接删除
      fs.unlinkSync(filePath);
    }
  }
  console.log(`已清空目录: ${assetsDir}`);
} else {
  // 如果目录不存在，创建它
  fs.mkdirSync(assetsDir, { recursive: true });
  console.log(`已创建目录: ${assetsDir}`);
}

// 确保templates目录存在
if (!fs.existsSync(templatesDir)) {
  fs.mkdirSync(templatesDir, { recursive: true });
  console.log(`已创建目录: ${templatesDir}`);
}

// 构建 Vue 应用
console.log('正在构建 Vue 应用...');
execSync('npx vite build', { stdio: 'inherit' });

// 生成随机文件名
function generateRandomFileName(extension) {
  // 生成16字节的随机数据并转换为十六进制字符串
  const randomBytes = crypto.randomBytes(16).toString('hex');
  return `${randomBytes}.${extension}`;
}

// 重命名文件并返回新文件名
function renameFileWithRandomName(directory, originalName, extension) {
  // 不重命名favicon.ico文件
  if (originalName === 'favicon.ico') {
    return originalName;
  }
  
  const newFileName = generateRandomFileName(extension);
  const oldPath = path.join(directory, originalName);
  const newPath = path.join(directory, newFileName);
  
  if (fs.existsSync(oldPath)) {
    fs.renameSync(oldPath, newPath);
    console.log(`文件已重命名: ${originalName} -> ${newFileName}`);
    return newFileName;
  } else {
    console.warn(`警告: 文件 ${originalName} 不存在，无法重命名`);
    return originalName;
  }
}

// 查找所有资源文件
const allFiles = fs.readdirSync(assetsDir);
const jsFiles = allFiles.filter(file => file.endsWith('.js'));
const cssFiles = allFiles.filter(file => file.endsWith('.css'));
const imageFiles = allFiles.filter(file => /\.(png|jpg|jpeg|gif|svg|webp)$/.test(file));
const otherFiles = allFiles.filter(file => 
  !file.endsWith('.js') && 
  !file.endsWith('.css') && 
  !/\.(png|jpg|jpeg|gif|svg|webp)$/.test(file) && 
  file !== 'favicon.ico'
);

// 重命名所有JS文件
const jsFileMap = {};
jsFiles.forEach(file => {
  const extension = path.extname(file).substring(1);
  const newFileName = renameFileWithRandomName(assetsDir, file, extension);
  jsFileMap[file] = newFileName;
});

// 重命名所有CSS文件
const cssFileMap = {};
cssFiles.forEach(file => {
  const extension = path.extname(file).substring(1);
  const newFileName = renameFileWithRandomName(assetsDir, file, extension);
  cssFileMap[file] = newFileName;
});

// 重命名所有图片文件
const imageFileMap = {};
imageFiles.forEach(file => {
  const extension = path.extname(file).substring(1);
  const newFileName = renameFileWithRandomName(assetsDir, file, extension);
  imageFileMap[file] = newFileName;
});

// 重命名其他文件
const otherFileMap = {};
otherFiles.forEach(file => {
  const extension = path.extname(file).substring(1);
  const newFileName = renameFileWithRandomName(assetsDir, file, extension);
  otherFileMap[file] = newFileName;
});

console.log(`检测到并重命名了文件:`);
console.log(`- JS文件: ${Object.keys(jsFileMap).length} 个`);
console.log(`- CSS文件: ${Object.keys(cssFileMap).length} 个`);
console.log(`- 图片文件: ${Object.keys(imageFileMap).length} 个`);
console.log(`- 其他文件: ${Object.keys(otherFileMap).length} 个`);

// 创建一个简单的 index.html 文件，引用构建后的资源
const indexContent = `
<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8">
    <link rel="icon" href="/assets/favicon.ico">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gemini API 代理服务</title>
    ${Object.values(jsFileMap).map(file => `<script type="module" crossorigin src="/assets/${file}"></script>`).join('\n    ')}
    ${Object.values(cssFileMap).map(file => `<link rel="stylesheet" href="/assets/${file}">`).join('\n    ')}
  </head>
  <body>
    <div id="app"></div>
  </body>
</html>
`;

// 将 index.html 写入到 app/templates 目录
const targetIndexPath = path.resolve(templatesDir, 'index.html');
fs.writeFileSync(targetIndexPath, indexContent);

console.log('构建完成！');
console.log(`- index.html 已创建到: ${targetIndexPath}`);
console.log(`- 静态资源已输出到: ${assetsDir}`);