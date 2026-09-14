/* eslint-disable prettier/prettier */
/* eslint-disable no-var */
var commonModule = {
  /**测试环境 */
  isDev: false,
  hostUrl: 'https://easyeda.com',
  hostUrlPro: 'https://pro.easyeda.com',
  // 数据下载eda
  onloadLceda: function (productCode) {
    let canvas = document.getElementById('root')
    let canvas2 = document.getElementById('root2')
    let gZoom = 1
    let gZoom2 = 1
    let gridSize = 10 //网格尺寸
    let historyClientXY_sch
    let historyClientXY_pcb
    let BBox_sch = { x: 0, y: 0, width: 366, height: 366 }
    let BBox_pcb = { x: 0, y: 0, width: 366, height: 366 }
    let isfirefox = navigator.userAgent.indexOf('Firefox') > 0 ? true : false
    let isEdge = navigator.userAgent.indexOf('Edge') > -1 ? true : false
    let isIE = !!window.ActiveXObject || 'ActiveXObject' in window ? true : false
    let LEFT = $('#root').offset().left
    let TOP = $('#root').offset().top
    let LEFT2 = $('#root2').offset().left
    let TOP2 = $('#root2').offset().top
    let N = 1,
      N2 = 1

    /**viewbox{x,y,height,width}*/
    function updateCanvas(viewBox) {
      /*if(!viewBox.x || !viewBox.y ||　!viewBox.width || !viewBox.height)
        return;*/
      let grid1 = $('#grid1'),
        gridOH = $('#gridOH'),
        gridOV = $('#gridOV')

      grid1.attr('x', viewBox.x)
      grid1.attr('y', viewBox.y)
      grid1.attr('width', viewBox.width)
      grid1.attr('height', viewBox.height)
      gridOH.attr('x1', viewBox.x)
      gridOH.attr('y1', 180)
      gridOH.attr('x2', viewBox.width + viewBox.x)
      gridOH.attr('y2', 180)
      gridOV.attr('x1', 180)
      gridOV.attr('y1', viewBox.y)
      gridOV.attr('x2', 180)
      gridOV.attr('y2', viewBox.height + viewBox.y)
    }

    function updateCanvas2(viewBox) {
      /*if(!viewBox.x || !viewBox.y ||　!viewBox.width || !viewBox.height)
        return;*/
      let grid1 = $('#grid12'),
        gridOH = $('#gridOH2'),
        gridOV = $('#gridOV2'),
        gridBg = $('#gridBg')

      grid1.attr('x', viewBox.x)
      grid1.attr('y', viewBox.y)
      grid1.attr('width', viewBox.width)
      grid1.attr('height', viewBox.height)
      gridOH.attr('x1', viewBox.x)
      gridOH.attr('y1', 180)
      gridOH.attr('x2', viewBox.width + viewBox.x)
      gridOH.attr('y2', 180)
      gridOV.attr('x1', 180)
      gridOV.attr('y1', viewBox.y)
      gridOV.attr('x2', 180)
      gridOV.attr('y2', viewBox.height + viewBox.y)
      gridBg.attr('x', viewBox.x)
      gridBg.attr('y', viewBox.y)
      gridBg.attr('width', viewBox.width)
      gridBg.attr('height', viewBox.height)
    }

    //移动事件
    $(document).on('mousedown', '#root', function (e_down_) {
      let e_down = e_down_.originalEvent
      let isdown = true
      let downX = e_down.offsetX,
        downY = e_down.offsetY
      if ((isfirefox || isIE || isEdge) && e_down.target.tagName !== 'svg') {
        downX = e_down.pageX - LEFT
        downY = e_down.pageY - TOP
      }
      $(document).on('mousemove', '#root', function (e_move_) {
        let e_move = e_move_.originalEvent
        if (isdown) {
          let moveX = e_move.offsetX,
            moveY = e_move.offsetY
          if ((isfirefox || isIE || isEdge) && e_move.target.tagName !== 'svg') {
            moveX = e_move.pageX - LEFT
            moveY = e_move.pageY - TOP
          }
          let dx = downX - moveX,
            dy = downY - moveY
          if (dx !== 0 && dy !== 0) {
            //更新viewBox
            let viewbox = canvas.viewBox.baseVal
            viewbox.x += dx / gZoom
            viewbox.y += dy / gZoom
            let viewBoxStr = viewbox.x + ' ' + viewbox.y + ' ' + viewbox.width + ' ' + viewbox.height
            canvas.setAttribute('viewBox', ' ' + viewBoxStr)
            //更新画布
            updateCanvas(viewbox)
            //刷新坐标
            downX = moveX
            downY = moveY
          }
        }
      })
      $(document).on('mouseup', '#root', function (e_up) {
        isdown = false
      })
    })
    $(document).on('mousedown', '#root2', function (e_down_) {
      let e_down = e_down_.originalEvent
      let isdown = true
      let downX = e_down.offsetX,
        downY = e_down.offsetY
      if ((isfirefox || isIE || isEdge) && e_down.target.tagName !== 'svg') {
        downX = e_down.pageX - LEFT2
        downY = e_down.pageY - TOP2
      }
      $(document).on('mousemove', '#root2', function (e_move_) {
        let e_move = e_move_.originalEvent
        if (isdown) {
          let moveX = e_move.offsetX,
            moveY = e_move.offsetY
          if ((isfirefox || isIE || isEdge) && e_move.target.tagName !== 'svg') {
            moveX = e_move.pageX - LEFT2
            moveY = e_move.pageY - TOP2
          }
          let dx = downX - moveX,
            dy = downY - moveY
          if (dx !== 0 && dy !== 0) {
            //更新viewBox
            let viewbox = canvas2.viewBox.baseVal
            viewbox.x += dx / gZoom2
            viewbox.y += dy / gZoom2
            let viewBoxStr = viewbox.x + ' ' + viewbox.y + ' ' + viewbox.width + ' ' + viewbox.height
            canvas2.setAttribute('viewBox', ' ' + viewBoxStr)
            //更新画布
            updateCanvas2(viewbox)
            //刷新坐标
            downX = moveX
            downY = moveY
          }
        }
      })
      $(document).on('mouseup', '#root2', function (e_up) {
        isdown = false
      })
    })
    //阻止右键菜单
    $(document).on('contextmenu', '#root', function (e) {
      e.preventDefault()
    })
    $(document).on('contextmenu', '#root2', function (e) {
      e.preventDefault()
    })

    //缩放事件
    $(document).on('mousewheel DOMMouseScroll', '#root', function (e) {
      let delta =
        (e.originalEvent.wheelDelta && (e.originalEvent.wheelDelta > 0 ? 1 : -1)) ||
        (e.originalEvent.detail && (e.originalEvent.detail > 0 ? -1 : 1))
      if (delta != 0) {
        let clientXY = {
          x: e.originalEvent.offsetX,
          y: e.originalEvent.offsetY
        }
        if ((isfirefox || isIE || isEdge) && e.target.tagName !== 'svg') {
          clientXY = {
            x: e.originalEvent.pageX - LEFT,
            y: e.originalEvent.pageY - TOP
          }
        }
        if (delta > 0) {
          zoom(100 * gZoom * 1.2, clientXY)
        } else {
          zoom((100 * gZoom) / 1.2, clientXY)
        }
      }
    })
    $(document).on('mousewheel DOMMouseScroll', '#root2', function (e) {
      let delta =
        (e.originalEvent.wheelDelta && (e.originalEvent.wheelDelta > 0 ? 1 : -1)) ||
        (e.originalEvent.detail && (e.originalEvent.detail > 0 ? -1 : 1))
      if (delta != 0) {
        let clientXY = {
          x: e.originalEvent.offsetX,
          y: e.originalEvent.offsetY
        }
        if ((isfirefox || isIE || isEdge) && e.target.tagName !== 'svg') {
          clientXY = {
            x: e.originalEvent.pageX - LEFT2,
            y: e.originalEvent.pageY - TOP2
          }
        }
        if (delta > 0) {
          zoom2(100 * gZoom2 * 1.2, clientXY)
        } else {
          zoom2((100 * gZoom2) / 1.2, clientXY)
        }
      }
    })
    /**
     clientXY{x,y}
     */
    function zoom(n, clientXY) {
      if (n > 3000 || n < 25) {
        return
      }
      let gZoomOld = gZoom
      gZoom = n / 100

      let vbNew
      let vbOld = canvas.viewBox.baseVal,
        W = +canvas.getAttribute('width'),
        H = +canvas.getAttribute('height')

      //鼠标在画布中（非边沿）的时候，使用鼠标点为中心缩放，否则使用bbox中心为中心缩放(手机上以屏幕中心缩放)
      if (clientXY) {
        vbNew = [
          vbOld.x + clientXY.x / gZoomOld - clientXY.x / gZoom,
          vbOld.y + clientXY.y / gZoomOld - clientXY.y / gZoom,
          W / gZoom,
          H / gZoom
        ]
        historyClientXY_sch = clientXY //记录
      } else {
        let bbox = BBox_sch
        svgXY = {
          x: bbox.width ? bbox.x + bbox.width / 2 : bbox.x || vbOld.x + vbOld.width / 2,
          y: bbox.height ? bbox.y + bbox.height / 2 : bbox.y || vbOld.y + vbOld.height / 2
        }
        //且要将缩放后的画面置于视野中心
        vbNew = [svgXY.x - W / gZoom / 2, svgXY.y - H / gZoom / 2, W / gZoom, H / gZoom]
      }

      let viewbox = {
        x: vbNew[0],
        y: vbNew[1],
        width: vbNew[2],
        height: vbNew[3]
      }
      let viewBoxStr = viewbox.x + ' ' + viewbox.y + ' ' + viewbox.width + ' ' + viewbox.height
      canvas.setAttribute('viewBox', ' ' + viewBoxStr)
      updateCanvas(viewbox)

      //细节调整
      let gridCell2 = document.getElementById('gridCell2'),
        gridOH = document.getElementById('gridOH'),
        gridOV = document.getElementById('gridOV')
      let px1 = 100 / n
      $(gridCell2).attr('stroke-width', px1)
      $(gridOH).attr('stroke-width', px1)
      $(gridOV).attr('stroke-width', px1)

      if (gridSize < 1) {
        gridSize = 1
      }
      while (gridSize * gZoom < 5) {
        if (gridSize * gZoom * 2 >= 5) {
          gridSize *= 2
        } else if (gridSize * gZoom * 5 >= 5) {
          gridSize *= 5
        } else {
          gridSize *= 10
        }
      }
      if (gZoom >= 1) {
        gridSize = 10
      }
      let gridPattern2 = document.getElementById('gridPattern2')
      $(gridPattern2).attr('width', gridSize)
      $(gridPattern2).attr('height', gridSize)
      $(gridCell2).attr('d', 'M10 0V10H0'.replace(/10/g, gridSize))
    }
    function zoom2(n, clientXY) {
      if (n > 3000 || n < 25) {
        return
      }
      let gZoomOld = gZoom2
      gZoom2 = n / 100

      let vbNew
      let vbOld = canvas2.viewBox.baseVal,
        W = +canvas2.getAttribute('width'),
        H = +canvas2.getAttribute('height')

      //鼠标在画布中（非边沿）的时候，使用鼠标点为中心缩放，否则使用bbox中心为中心缩放(手机上以屏幕中心缩放)
      if (clientXY) {
        vbNew = [
          vbOld.x + clientXY.x / gZoomOld - clientXY.x / gZoom2,
          vbOld.y + clientXY.y / gZoomOld - clientXY.y / gZoom2,
          W / gZoom2,
          H / gZoom2
        ]
        historyClientXY_pcb = clientXY //记录
      } else {
        let bbox = BBox_pcb
        svgXY = {
          x: bbox.width ? bbox.x + bbox.width / 2 : bbox.x || vbOld.x + vbOld.width / 2,
          y: bbox.height ? bbox.y + bbox.height / 2 : bbox.y || vbOld.y + vbOld.height / 2
        }
        //且要将缩放后的画面置于视野中心
        vbNew = [svgXY.x - W / gZoom2 / 2, svgXY.y - H / gZoom2 / 2, W / gZoom2, H / gZoom2]
      }

      let viewbox = {
        x: vbNew[0],
        y: vbNew[1],
        width: vbNew[2],
        height: vbNew[3]
      }
      let viewBoxStr = viewbox.x + ' ' + viewbox.y + ' ' + viewbox.width + ' ' + viewbox.height
      canvas2.setAttribute('viewBox', ' ' + viewBoxStr)
      updateCanvas2(viewbox)

      //细节调整
      let gridCell2 = document.getElementById('gridCell22'),
        gridOH = document.getElementById('gridOH2'),
        gridOV = document.getElementById('gridOV2')
      let px1 = 100 / n
      $(gridCell2).attr('stroke-width', px1)
      $(gridOH).attr('stroke-width', px1)
      $(gridOV).attr('stroke-width', px1)

      if (gridSize < 1) {
        gridSize = 1
      }
      while (gridSize * gZoom2 < 5) {
        if (gridSize * gZoom2 * 2 >= 5) {
          gridSize *= 2
        } else if (gridSize * gZoom2 * 5 >= 5) {
          gridSize *= 5
        } else {
          gridSize *= 10
        }
      }
      if (gZoom2 >= 1) {
        gridSize = 10
      }
      let gridPattern2 = document.getElementById('gridPattern22')
      $(gridPattern2).attr('width', gridSize)
      $(gridPattern2).attr('height', gridSize)
      $(gridCell2).attr('d', 'M10 0V10H0'.replace(/10/g, gridSize))
    }

    //控制按钮
    $(document).on('click', '#rootlarger', function (event) {
      zoom(1.2 * gZoom * 100, historyClientXY_sch)
    })
    $(document).on('click', '#rootsmaller', function (event) {
      zoom((gZoom / 1.2) * 100, historyClientXY_sch)
    })
    $(document).on('click', '#rootreset', resetRootCanvas)
    //控制按钮2
    $(document).on('click', '#rootlarger2', function (event) {
      zoom2(1.2 * gZoom2 * 100, historyClientXY_pcb)
    })
    $(document).on('click', '#rootsmaller2', function (event) {
      zoom2((gZoom2 / 1.2) * 100, historyClientXY_pcb)
    })
    $(document).on('click', '#rootreset2', resetRootCanvas2)

    $(document).on('click', '#userButton', function (e) {
      if (e.target.tagName === 'div' || e.target.tagName === 'DIV') $('#userButton a')[0].click()
    })

    /*重置当前画布到初始化时的样子：方便预览*/
    function resetRootCanvas() {
      let zn = 100 * N * 0.8
      zn = zn > 3000 ? 3000 : zn
      zn = zn < 25 ? 25 : zn
      zoom(zn)
    }
    function resetRootCanvas2() {
      let zn = 100 * N2 * 0.8
      zn = zn > 3000 ? 3000 : zn
      zn = zn < 25 ? 25 : zn
      zoom2(zn)
    }

    function svgStrFilter(svgStr) {
      svgStr = svgStr.replace(/^<svg.*?>/, '')
      if (svgStr.indexOf('</style>') >= 0) {
        svgStr = svgStr.split('</style>')[1]
      }
      return svgStr.replace('</svg>', '')
    }

    //申请设计
    function requestDesign(number) {
      let getUse = $('#getUse')
      getUse.text('Require New Part')
      let url = commonModule.hostUrl + '/page/apply-new-part' + '?code=' + number
      getUse.attr('href', url)
      let button = $('#userButton a')
      button.text('Require New Part')
      button.attr('href', url)
      let schCanvas = $('#schCanvas')
      let pcbCanvas = $('#pcbCanvas')
      schCanvas.html('<div class="requestDesign">Not Design Yet...</div>')
      pcbCanvas.html('<div class="requestDesign">Not Design Yet...</div>')
    }

    //根据商品编号获取数据
    function getDataByNumber(number) {
      let reportError = commonModule.hostUrl + '/page/report-part-error' + '?code=' + number
      $('#reportError').attr('href', reportError)
      let url = commonModule.hostUrl + '/api/products/' + number + '/svgs'
      $.ajax({
        url: url,
        type: 'GET',
        async: true,
        timeout: 5000
      }).then(
        function (res) {
          if (res.success) {
            let data = res.result
            if (data.length === 0) {
              //替换相关显示信息
              requestDesign(number)
            } else {
              $('#reportError').show()
              //1.接收数据并处理
              let sch_len = 0,
                pcb_len = 0
              let maxWidth = 0,
                maxHeight = 0
              let bboxArr = []
              let svgStr = '',
                sch_svgStr = '',
                pcb_svgStr = ''
              let RC = {}
              let pcb_index = 1
              let indexType = 2
              let uuid = '#libs=',
                uuidArr = []
              let pcb_uuid = ''
              for (var i = 0; i < data.length; i++) {
                if (data[i].docType === 6) {
                  indexType = 6
                  break
                }
              }
              for (i = 0; i < data.length; i++) {
                svgStr = data[i].svg
                svgStr = svgStrFilter(svgStr)
                svgStr = '<g>' + svgStr + '</g>'

                if (data[i].docType === indexType) {
                  sch_len++
                  svgStr = svgStr.replace('fill="#FFFFFF"', 'fill="none"')
                  svgStr = svgStr.replace('fill="#ffffff"', 'fill="none"')
                  svgStr = svgStr.replace('fill="white"', 'fill="none"')
                  sch_svgStr += svgStr

                  let bbox = data[i].bbox
                  bboxArr.push(bbox)
                  maxWidth = bbox.width > maxWidth ? bbox.width : maxWidth
                  maxHeight = bbox.height > maxHeight ? bbox.height : maxHeight

                  uuidArr.push(data[i].component_uuid)
                } else if (data[i].docType === 4) {
                  svgStr = svgStr.replace('fill="#000000"', 'fill="none"')
                  svgStr = svgStr.replace('fill="black"', 'fill="none"')
                  pcb_len++
                  pcb_svgStr += svgStr
                  pcb_index = i
                  pcb_uuid = data[i].component_uuid
                }
              }
              $('#g1').html(sch_svgStr)
              $('#g12').html(pcb_svgStr)
              let spacing = 10 //间距默认为10
              RC = getSquareRowCol(sch_len, maxWidth, maxHeight, spacing)

              BBox_sch = {
                x: 0,
                y: 0,
                width: RC.width,
                height: RC.height
              }
              let Length = BBox_sch.width > BBox_sch.height ? BBox_sch.width : BBox_sch.height
              N = 366 / Length
              resetRootCanvas()
              if (data[pcb_index].bbox.width) BBox_pcb = data[pcb_index].bbox
              let Length2 = BBox_pcb.width > BBox_pcb.height ? BBox_pcb.width : BBox_pcb.height
              N2 = 366 / Length2
              resetRootCanvas2()

              uuid += '&' + uuidArr[0]
              for (i = 1; i < uuidArr.length; i++) {
                uuid += '|&' + uuidArr[i]
              }
              // 需要把pcb的uuid也拼接上去
              uuid += '|!' + pcb_uuid
              // 更新文档跳转连接
              // 标准版连接（旧）
              $('#userButton a').attr('href', commonModule.hostUrl + '/editor' + uuid)
              $('#getUse').attr('href', commonModule.hostUrl + '/editor' + uuid)
              // 引流到专业版的连接(新)
              $.ajax({
                url: commonModule.hostUrlPro + '/api/devices/searchByCodes',
                type: 'POST',
                data: {
                  codes: [number]
                },
                async: true,
                timeout: 5000
              }).then(function (proRes) {
                let proResult = proRes && proRes.result
                if (!Array.isArray(proResult)) {
                  return
                }
                let deviceUuid = '',
                  symbolUuid = '',
                  fooprintUuid = ''
                proResult.some(function (item) {
                  let attrs = item.attributes
                  if (attrs.Symbol && attrs.Footprint) {
                    fetRes(item)
                    return true
                  }
                  return false
                })
                if (!deviceUuid) {
                  deviceUuid = fetRes(proResult[0])
                }
                if (!fooprintUuid && !symbolUuid) {
                  return
                }
                // 拼接
                let proUrl = commonModule.hostUrlPro + '/editor#tab=*'
                if (symbolUuid) {
                  proUrl += '!' + symbolUuid
                  if (deviceUuid) {
                    proUrl += `(device)${deviceUuid}`
                  }
                }
                if (fooprintUuid) {
                  if (symbolUuid) {
                    proUrl += '|'
                  }
                  proUrl += '!' + fooprintUuid
                  if (deviceUuid) {
                    proUrl += `(device)${deviceUuid}`
                  }
                }
                $('#userButton a').attr('href', proUrl)
                $('#getUse').attr('href', proUrl)

                function fetRes(item) {
                  if (!item) {
                    return
                  }
                  let attrs = item.attributes
                  deviceUuid = item.uuid
                  symbolUuid = attrs && attrs.Symbol
                  fooprintUuid = attrs && attrs.Footprint
                }
              })

              //2.排列
              let sch_g = $('#g1 > g')
              let dx = 0,
                dy = 0
              let row_now = 1,
                col_now = 1
              for (i = 0; i < sch_g.length; i++) {
                if (col_now > RC.col) {
                  row_now++
                  col_now = 1
                }
                dx =
                  BBox_sch.x - bboxArr[i].x + (maxWidth - bboxArr[i].width) / 2 + (col_now - 1) * (maxWidth + spacing)
                dy = BBox_sch.y - bboxArr[i].y + (row_now - 1) * (maxHeight + spacing)
                SVGMove.g(sch_g[i], dx, dy)

                col_now++
              }

              //3、为焊盘添加编号
              let pads = $('#g12 g[c_partid="part_pad"]')
              let textTemp = $('#textTemp')
              let gNets = $('#gNets')
              let originXY, originxy, textEle, num
              for (i = 0; i < pads.length; i++) {
                originXY = pads[i].getAttribute('c_origin')
                num = pads[i].getAttribute('number')
                if (originXY) {
                  originXY = originXY.split(',')
                }
                if (originXY.length > 1) {
                  textEle = textTemp[0].cloneNode(true)
                  textEle.setAttribute('x', originXY[0])
                  textEle.setAttribute('y', originXY[1])
                  textEle.innerHTML = num
                  gNets.append(textEle)
                }
              }

              //4、显示引脚标号和名称
              let schPins = $('#g1 g[c_partid="part_pin"] > text')
              for (i = 0; i < schPins.length; i++) {
                attr(schPins[i], 'display', '')
                attr(schPins[i], 'font-size', '4pt')
              }
            }
          } else {
            loadErrorShowContent(number)
          }
        },
        function (err) {
          loadErrorShowContent(number)
        }
      )
    }

    function loadErrorShowContent(number) {
      if (getUrlParam('detail')) {
        const iframe = $(window.parent.document).contents().find('iframe.border-none')[0]
        iframe.style.height = '40px'
        const hintDownDom = $('#hint_down')
        hintDownDom.css({
          border: 'none',
          'margin-top': '20px',
          'margin-bottom': '40px'
        })
        hintDownDom.html(
          '<div class="load-err">\n' +
            '        <img src="./lib/attention_icon@2x.png" width="17px" height="17px" style="margin-right: 8px;" alt="">\n' +
            '        Currently, there is no library. You can\n' +
            '        <a href="https://easyeda.com/page/apply-new-part" target="_blank">request free CAD model design at EasyEDA.</a>\n' +
            '      </div>'
        )
      } else {
        requestDesign(number)
      }
    }

    if (!isIE) {
      getDataByNumber(productCode)
    } else {
      // ie8
      let explorer = window.navigator.userAgent.toLowerCase()
      if (explorer.indexOf('msie') >= 0) {
        let ver = explorer.match(/msie ([\d.]+)/)[1]
        if (ver < 9) {
          $('#lcedalogo a:eq(0)').html('<div style="height: 45px;width: 180px;margin-top:0;margin-left:30px;"></div>')
        }
      }
      let getUse = $('#getUse')
      getUse.attr('href', commonModule.hostUrl + '/editor')
      let button = $('#userButton a')
      button.attr('href', commonModule.hostUrl + '/editor')
      let schCanvas = $('#schCanvas')
      let pcbCanvas = $('#pcbCanvas')
      schCanvas.html(
        '<div class="requestDesign">Does not support IE browser,</div><div style="text-align: center;font-size: 16px;font-weight: bold;">please use Chrome or Firefox or Edge</div>'
      )
      pcbCanvas.html(
        '<div class="requestDesign">Does not support IE browser,</div><div style="text-align: center;font-size: 16px;font-weight: bold;">please use Chrome or Firefox or Edge</div>'
      )

      let url = commonModule.hostUrl + '/api/products/' + productCode + '/svgs'
      $.ajax({
        url: url,
        type: 'GET',
        async: false
      }).then(function (res) {
        let uuid = '#libs=',
          uuidArr = [],
          pcb_uuid
        if (res.success) {
          let data = res.result
          if (data.length === 0) {
            return
          } else {
            let indexType = 2
            // eslint-disable-next-line no-var
            for (var i = 0; i < data.length; i++) {
              if (data[i].docType === 6) {
                indexType = 6
                break
              }
            }
            for (i = 0; i < data.length; i++) {
              if (data[i].docType === indexType) {
                uuidArr.push(data[i].component_uuid)
              } else if (data[i].docType === 4) {
                pcb_uuid = data[i].component_uuid
              }
            }
            uuid += '&' + uuidArr[0]
            for (i = 1; i < uuidArr.length; i++) {
              uuid += '|&' + uuidArr[i]
            }
            //需要把pcb的uuid也拼接上去
            uuid += '|!' + pcb_uuid

            $('#userButton a').attr('href', commonModule.hostUrl + '/editor' + uuid)
            $('#getUse').attr('href', commonModule.hostUrl + '/editor' + uuid)
          }
        } else {
          return
        }
      })
    }
  }
}

function getUrlParam(name) {
  const searchParams = new URLSearchParams(window.location.search)
  return searchParams.get(name)
}

let num = getUrlParam('code') || 'C309064'
commonModule.onloadLceda(num)

// 本地测试
if (commonModule.isDev) {
  commonModule.hostUrl = 'https://dev.lceda.cn'
  commonModule.hostUrlPro = 'https://devpro.lceda.cn'
  let num = window.location.search.split('?')[1] || 'C309064'
  commonModule.onloadLceda(num)
}
