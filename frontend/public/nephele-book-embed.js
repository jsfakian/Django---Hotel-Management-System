/**
 * Nephele booking-engine embed snippet.
 *
 * Usage:
 *   <div id="nephele-book" data-property-id="1" data-height="720"></div>
 *   <script src="https://YOUR_HOST/nephele-book-embed.js" async></script>
 *
 * Optional data attributes on the host element:
 *   data-property-id  (required)  Property PK
 *   data-base-url     Origin of the Nephele SPA (default: script origin)
 *   data-height       iframe height in px (default: 720)
 *   data-lang         en | el
 */
(function () {
  'use strict'

  function scriptOrigin() {
    var scripts = document.getElementsByTagName('script')
    for (var i = scripts.length - 1; i >= 0; i -= 1) {
      var src = scripts[i].src || ''
      if (src.indexOf('nephele-book-embed.js') !== -1) {
        try {
          return new URL(src).origin
        } catch (e) {
          break
        }
      }
    }
    return window.location.origin
  }

  function mount(el) {
    if (!el || el.getAttribute('data-nephele-mounted') === '1') return
    var propertyId = el.getAttribute('data-property-id') || ''
    if (!propertyId) {
      el.textContent = 'Nephele embed: missing data-property-id'
      return
    }
    var base = (el.getAttribute('data-base-url') || scriptOrigin()).replace(/\/$/, '')
    var height = el.getAttribute('data-height') || '720'
    var lang = el.getAttribute('data-lang') || ''
    var src =
      base +
      '/book/embed?property_id=' +
      encodeURIComponent(propertyId) +
      (lang ? '&lang=' + encodeURIComponent(lang) : '')

    var iframe = document.createElement('iframe')
    iframe.src = src
    iframe.title = 'Nephele booking'
    iframe.style.cssText = 'width:100%;border:0;display:block;height:' + height + 'px'
    iframe.setAttribute('loading', 'lazy')
    iframe.setAttribute('referrerpolicy', 'no-referrer-when-downgrade')

    window.addEventListener('message', function (event) {
      if (!event || !event.data || event.data.source !== 'nephele-book') return
      if (event.data.type === 'resize' && event.data.height) {
        iframe.style.height = Math.max(480, Number(event.data.height) || 720) + 'px'
      }
    })

    el.innerHTML = ''
    el.appendChild(iframe)
    el.setAttribute('data-nephele-mounted', '1')
  }

  function boot() {
    var nodes = document.querySelectorAll('[data-nephele-book], #nephele-book')
    for (var i = 0; i < nodes.length; i += 1) mount(nodes[i])
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot)
  } else {
    boot()
  }
})()
