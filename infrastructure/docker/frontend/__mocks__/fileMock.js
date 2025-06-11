// ==============================================================================
// Mine-CMS ファイルモック
// ==============================================================================
// このファイルは、Jest でテストを実行する際に、画像やフォントなどの
// 静的ファイルをモックするために使用されます。
//
// なぜこれが必要なのか：
// - Webpack は画像ファイルを JavaScript モジュールとして扱えますが、
//   Jest（Node.js環境）はデフォルトでは画像ファイルを理解できません
// - このモックファイルにより、画像のインポートがエラーにならずに
//   テストを実行できるようになります
//
// 使用例：
// コンポーネント内で:
//   import logo from './logo.png'
//   <img src={logo} alt="Logo" />
//
// テスト実行時:
//   logo は 'test-file-stub' という文字列になります
// ==============================================================================

// シンプルなモック：ファイルパスを文字列として返す
// これは最も基本的なモックで、多くの場合はこれで十分です
module.exports = "test-file-stub";

// ==============================================================================
// より高度なモックの例（必要に応じてコメントアウトを解除して使用）
// ==============================================================================

// 例1: ファイル名を含むモック
// ファイル名に基づいたテストを行いたい場合に有用です
/*
module.exports = {
  // webpack のように、元のファイル名を保持
  __esModule: true,
  default: 'test-file-stub',
  // ファイル情報を含むオブジェクトを返すこともできます
  src: 'test-file-stub',
  height: 100,
  width: 100,
  // テスト用の追加プロパティ
  testId: 'mocked-image',
}
*/

// 例2: 動的モック（ファイルパスに応じて異なる値を返す）
// より複雑なテストシナリオで使用できます
/*
const path = require('path')

module.exports = new Proxy(
  {},
  {
    get(target, key) {
      if (key === '__esModule') {
        return true
      }
      // ファイル名から拡張子を除いた部分を返す
      return key.toString()
    },
  }
)
*/

// 例3: React コンポーネントとしてのモック
// 画像を React コンポーネントとして扱いたい場合
/*
const React = require('react')

module.exports = {
  __esModule: true,
  default: (props) =>
    React.createElement('img', {
      ...props,
      src: 'test-file-stub',
    }),
}
*/

// ==============================================================================
// メディアタイプ別の詳細なモック（高度な使用例）
// ==============================================================================
/*
const path = require('path')

// ファイル拡張子に基づいて異なるモックを返す
module.exports = (filePath) => {
  const ext = path.extname(filePath).toLowerCase()
  
  switch (ext) {
    case '.png':
    case '.jpg':
    case '.jpeg':
    case '.gif':
    case '.webp':
      return {
        src: `mocked-image${ext}`,
        height: 100,
        width: 100,
        alt: 'Mocked Image',
      }
      
    case '.svg':
      // SVG は React コンポーネントとして使われることがある
      return {
        ReactComponent: () => React.createElement('svg'),
        default: `mocked-svg${ext}`,
      }
      
    case '.mp4':
    case '.webm':
      return {
        src: `mocked-video${ext}`,
        duration: 120,
        type: `video/${ext.slice(1)}`,
      }
      
    case '.mp3':
    case '.wav':
      return {
        src: `mocked-audio${ext}`,
        duration: 180,
        type: `audio/${ext.slice(1)}`,
      }
      
    case '.woff':
    case '.woff2':
    case '.ttf':
    case '.eot':
      return `mocked-font${ext}`
      
    default:
      return 'test-file-stub'
  }
}
*/
