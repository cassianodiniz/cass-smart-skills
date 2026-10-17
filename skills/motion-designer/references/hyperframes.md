# HTML + GSAP + HyperFrames

A base em `assets/base.html` contém atributos de composição e registra uma timeline GSAP pausada em `window.__timelines.main`. Use uma composição única; quando separar cenas em elementos `.clip`, declare início, duração e `data-track-index` conforme o HyperFrames.

Antes de animar, defina estados iniciais com `tl.set(..., 0)`. Animações posteriores que reutilizam o mesmo elemento precisam de `immediateRender:false` para não antecipar o estado de outra cena. Centralização de elementos que recebem transformações GSAP: CSS `left:50%` com GSAP `xPercent:-50`, sem misturar `transform:translateX(-50%)` no CSS.

Exemplo para uma composição de 7 segundos, inserido na base:

```html
<!-- Dentro de #root -->
<div id="documento" style="position:absolute;left:50%;top:300px;width:200px;height:280px;background:#fff;border:6px solid #EFA819;border-radius:20px"></div>
```

```js
// Depois de criar tl, antes de registrar window.__timelines.main
tl.set('#documento', { xPercent:-50, y:80, opacity:0 }, 0);
tl.to('#documento', { y:0, opacity:1, duration:0.6, ease:'power3.out' }, 0);
tl.to('#documento', { scale:1.08, duration:0.5, immediateRender:false }, 2.4);
tl.to('#documento', { scale:1, duration:0.5, immediateRender:false }, 5.8);
tl.to({}, { duration:0.7 }, 6.3); // segura a duração total até 7 s
```

Este é um exemplo mínimo de estrutura, não a régua visual da entrega. Crie cenas com hierarquia, profundidade e variação de enquadramento conforme a fala. Evite JavaScript que depende do relógio real, aleatoriedade sem semente e recursos remotos na composição final; o motor precisa conseguir saltar para qualquer quadro.

Para conferir antes do MP4, use `check` e `snapshot --describe false` (impede análise externa automática quando uma chave de Gemini existe no ambiente). Os quadros de preview ajudam a revisar, mas a prova final é o arquivo renderizado. Inspecte o início, transições, final e redução a 360 px de largura.

Se a referência for um print, mova o enquadramento sobre o arquivo real e preserve seu cabeçalho no primeiro zoom. Se houver vídeo, prepare em SDR de 8 bits (`yuv420p`); HDR requer conversão de cor, não apenas trocar o formato dos pixels. Lint ou check não comprovam sincronização com a fala: compare a sequência com os tempos do trecho.
