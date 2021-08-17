function load(){
      const rows = {
        len: 100,
        0: {
          cells: {
            0: { text: 'SKU'},
            1: { text: 'QTY'},
            2: { text: 'UOM'},
          },

        }
      };
      for (let i = 1; i < 100; i += 1) {
        rows[i] = {
          cells: {
            1: { text: '1'},
            2: { text: 'EA'},
          }
        };
      }

      // x_spreadsheet.locale('zh-cn');
      var saveIcon = 'data:image/svg+xml;base64,PD94bWwgdmVyc2lvbj0iMS4wIiA/PjxzdmcgaGVpZ2h0PSIyNCIgdmVyc2lvbj0iMS4xIiB3aWR0aD0iMjQiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIgeG1sbnM6Y2M9Imh0dHA6Ly9jcmVhdGl2ZWNvbW1vbnMub3JnL25zIyIgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIiB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiPjxnIHRyYW5zZm9ybT0idHJhbnNsYXRlKDAgLTEwMjguNCkiPjxwYXRoIGQ9Im0zIDEwMzcuNHYyIDIgNmMwIDEuMSAwLjg5NTQgMiAyIDJoMTRjMS4xMDUgMCAyLTAuOSAyLTJ2LTYtMi0yaC0xOHoiIGZpbGw9IiMyOTgwYjkiLz48cGF0aCBkPSJtNSAzYy0xLjEwNDYgMC0yIDAuODk1NC0yIDJ2MiAyIDEgMiA2YzAgMS4xMDUgMC44OTU0IDIgMiAyaDE0YzEuMTA1IDAgMi0wLjg5NSAyLTJ2LTYtMi0xLTItMWwtMy0zaC0xLTItMTB6IiBmaWxsPSIjMzQ5OGRiIiB0cmFuc2Zvcm09InRyYW5zbGF0ZSgwIDEwMjguNCkiLz48cGF0aCBkPSJtNiAzdjEgMSAyYzAgMS4xMDQ2IDAuODk1NCAyIDIgMmgxIDQgMiAxYzEuMTA1IDAgMi0wLjg5NTQgMi0ydi0xLjg0MzgtMC4xNTYyLTEtMWgtMTJ6IiBmaWxsPSIjMjk4MGI5IiB0cmFuc2Zvcm09InRyYW5zbGF0ZSgwIDEwMjguNCkiLz48cGF0aCBkPSJtOCAxMDQxLjRjLTEuMTA0NiAwLTIgMC45LTIgMnYxLjggMy4yaDEydi0zLjItMS44YzAtMS4xLTAuODk1LTItMi0yaC0zLTV6IiBmaWxsPSIjZWNmMGYxIi8+PHJlY3QgZmlsbD0iI2JkYzNjNyIgaGVpZ2h0PSIxIiB3aWR0aD0iMTIiIHg9IjYiIHk9IjEwNDguNCIvPjxwYXRoIGQ9Im03IDEwMzEuNHYxIDJjMCAxLjEgMC44OTU0IDIgMiAyaDEgNCAxYzEuMTA1IDAgMi0wLjkgMi0ydi0xLjktMC4xLTFoLTEweiIgZmlsbD0iI2VjZjBmMSIvPjxwYXRoIGQ9Im04IDR2MmMwIDAuNTUyMyAwLjQ0NzcgMSAxIDFoMSAxYzAuNTUyIDAgMS0wLjQ0NzcgMS0xdi0yaC0yLTJ6IiBmaWxsPSIjOTVhNWE2IiB0cmFuc2Zvcm09InRyYW5zbGF0ZSgwIDEwMjguNCkiLz48ZyBmaWxsPSIjYmRjM2M3Ij48cmVjdCBoZWlnaHQ9IjEiIHRyYW5zZm9ybT0idHJhbnNsYXRlKDAgMTAyOC40KSIgd2lkdGg9IjgiIHg9IjgiIHk9IjE1Ii8+PHJlY3QgaGVpZ2h0PSIxIiB3aWR0aD0iOCIgeD0iOCIgeT0iMTA0NS40Ii8+PHJlY3QgaGVpZ2h0PSIxIiB3aWR0aD0iNCIgeD0iOCIgeT0iMTAzMS40Ii8+PC9nPjwvZz48L3N2Zz4='
      var xs = x_spreadsheet('#x-spreadsheet-demo', {showToolbar: true, showGrid: true,
      row: {
        len: 100,
      },
      col: {
        len: 13,
        width: 100,
        indexWidth: 60,
        minWidth: 60,
        },
      showBottomBar: true,
      extendToolbar: {
          left: [
            {
              tip: 'Save',
              icon: saveIcon,
              onClick: (data, sheet) => {
              console.log('click save button：', data, sheet)
              $('#myModal').show();
              $("#myModalClose").click(function () {
                    $('#myModal').hide();
              });
              $("#errorModalClose").click(function () {
                    $('#errorModal').hide();
                    window.location.assign("/spreadsheet/stockhawk_submission");
              });
              $("#myModalOK").click(function () {
                    console.log(data);
                    console.log(sheet);
                    $('#myModal').hide();
                    $('#loader').show();
                    $.ajax({
                        url: "/spreadsheet/process_data",
                        type: "POST",
                        data: JSON.stringify({'data': data, 'sheet':sheet}),
                        dataType: "json",
                        traditional: true,
                        contentType: "application/json; charset=utf-8",
                        success: function (data) {
                                console.log(data);
                                if(data['result']['errorCode'] == 501){
                                    $('#loader').hide();
                                    window.location.assign("/my/orders/"+data['result']['orderId']+"?access_token="+data['result']['accessToken']);
                                }else{
                                    $('#loader').hide();
                                    $('#errorModal').show();
                                    $('#errorMessageDisplay').html(data['result']['message']);
                                }
                        }
                    });
              });
            }
           }
          ],
        }
        })
        .loadData([{
          styles: [
            {
              bgcolor: '#f4f5f8',
              textwrap: true,
              color: '#900b09',
            },
          ],
          cols: {
            len: 10,
            1: { width: 200 },
            2: { width: 120 },
          },
          rows,
        }]).change((cdata));

      setTimeout(() => {
      }, 50000);
    }

