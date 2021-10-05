function load(){
      const rows = {
        len: 101,
        0: {
          cells: {
            0: { text: 'SKU'},
            1: { text: 'QTY'},
            2: { text: 'UOM'},
          },

        }
      };
      for (let i = 1; i < 101; i += 1) {
        rows[i] = {
          cells: {
            1: { text: '1'},
            2: { text: 'EA'},
          }
        };
      }

      // x_spreadsheet.locale('zh-cn');
      var saveIcon = 'data:image/svg+xml;base64,PHN2ZyB2ZXJzaW9uPSIxLjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIgd2lkdGg9IjU3Ni4wMDAwMDBwdCIgaGVpZ2h0PSIxODkuMDAwMDAwcHQiIHZpZXdCb3g9IjAgMCA1NzYuMDAwMDAwIDE4OS4wMDAwMDAiIHByZXNlcnZlQXNwZWN0UmF0aW89InhNaWRZTWlkIG1lZXQiPgo8bWV0YWRhdGE+CkNyZWF0ZWQgYnkgcG90cmFjZSAxLjEwLCB3cml0dGVuIGJ5IFBldGVyIFNlbGluZ2VyIDIwMDEtMjAxMQo8L21ldGFkYXRhPgo8ZyB0cmFuc2Zvcm09InRyYW5zbGF0ZSgwLjAwMDAwMCwxODkuMDAwMDAwKSBzY2FsZSgwLjEwMDAwMCwtMC4xMDAwMDApIiBmaWxsPSIjYTMyNjI0IiBzdHJva2U9Im5vbmUiPgo8cGF0aCBkPSJNMzEwIDE3MzIgYy0yOSAtMTAgLTY1IC0zNiAtMTAxIC03MSAtOTIgLTkzIC04OSAtNjggLTg5IC03MjYgMCYjMTA7LTY1OCAtMyAtNjMzIDg5IC03MjYgOTkgLTk5IC0xODIgLTg5IDI2NDYgLTg5IDI4MjggMCAyNTQ3IC0xMCAyNjQ2IDg5IDkyIDkzJiMxMDs4OSA2OCA4OSA3MjYgMCA2NTggMyA2MzMgLTg5IDcyNiAtOTkgOTkgMTg0IDg5IC0yNjUzIDg4IC0yMjIxIC0xIC0yNDk4IC0zJiMxMDstMjUzOCAtMTd6IG0yMjI5IC0zMzYgYzkgLTEwIDEyIC01OCAxMSAtMTQ4IC0yIC0xNjEgLTIgLTE1NyAxMyAtMTM3IDMxIDQwJiMxMDs3MCA1NCAxNTIgNTQgODAgMCA4MyAtMSAxMjkgLTM5IDI2IC0yMSA1MCAtNDYgNTMgLTU1IDMgLTkgMTMgLTI0IDIyIC0zNSAxMiYjMTA7LTE0IDE2IC00MSAxNiAtMTE1IDAgLTEzMiAtMjggLTE5MCAtMTIwIC0yNDkgLTM0IC0yMiAtNTIgLTI2IC0xMTYgLTI3IC01NyAwJiMxMDstODIgNCAtOTUgMTYgLTMzIDI4IC01NSAzMSAtNjEgOSAtMyAtMTMgLTE3IC0yMiAtMzkgLTI2IC02NiAtMTIgLTY0IC0yMSAtNjQmIzEwOzM4MCAwIDI2OCAzIDM2NSAxMiAzNzQgMTcgMTcgNzMgMTUgODcgLTJ6IG0tODc3IC0yMiBjNTEgLTkgODAgLTM3IDcyIC03MiYjMTA7LTEwIC00MiAtMzEgLTU0IC02NSAtMzcgLTE2IDkgLTU2IDE1IC05MyAxNSAtNTkgMCAtNjkgLTMgLTEwMSAtMzEgLTQxIC0zNyYjMTA7LTQ1IC03MSAtMTIgLTExMCAyMSAtMjYgOTEgLTY5IDExMSAtNjkgMjYgMCAxMDUgLTQ5IDE0MyAtODcgNDUgLTQ3IDYxIC0xMDAmIzEwOzUwIC0xNjkgLTggLTUxIC01NiAtMTE0IC0xMDcgLTE0MiAtNDAgLTIyIC01NyAtMjUgLTE1MCAtMjYgLTExNiAtMSAtMTkwIDIxJiMxMDstMTkwIDU1IDAgNTQgNDcgODggNzggNTcgNyAtNyA1MSAtMTQgMTAyIC0xNiBsOTAgLTQgMzUgMzYgYzczIDc4IDI1IDE2MSYjMTA7LTExNCAyMDEgLTQ0IDEzIC0xMTggNjQgLTE0NiAxMDEgLTM4IDUwIC00NSAxMjcgLTE2IDE4NiAyMSA0NSA4NyA5NyAxNDAgMTA5JiMxMDszNSA5IDEyOCAxMCAxNzMgM3ogbTIzNDAgLTEyIGMxOSAtMTkgMTkgLTY4IDEgLTg5IC0yOCAtMzIgLTU2IC0zNiAtODYgLTEyJiMxMDstNTcgNDQgLTIxIDEyOCA0OCAxMTQgMTYgLTMgMzMgLTkgMzcgLTEzeiBtMjgzIC03MiBjNCAtMTEgNSAtNDAgNCAtNjMgLTQmIzEwOy01NSAzIC02NSA0MCAtNTkgMTcgMiA0NyAxIDY2IC0yIDMwIC02IDM1IC0xMSAzNSAtMzQgMCAtNDEgLTE3IC01MiAtODIgLTUyJiMxMDtsLTU4IDAgMCAtMTQ4IGMwIC0xNzMgNyAtMTkyIDY5IC0xOTIgMjkgMCA0MCAtNSA1MCAtMjQgMjAgLTM2IDYgLTY0IC0zNSAtNzImIzEwOy02NCAtMTIgLTExNCAxIC0xNTMgNDAgbC0zNiAzNiAtMyAxODAgLTQgMTgwIC0yNyAwIGMtMzQgMCAtNTEgMTcgLTUxIDUxIDAmIzEwOzIwIDYgMjggMjUgMzMgMTQgNCAzMCA0IDM1IDEgMTUgLTkgMjQgMTcgMjEgNjEgLTIgMzMgMyA0NyAyMCA2MyAzMCAyNyA3NSAyOCYjMTA7ODQgMXogbS0yMzQ3IC0xMzIgYzggLTggMTIgLTYwIDEyIC0xNjggMCAtMTY4IDggLTIwNCA1MyAtMjM1IDI4IC0yMCA5MCAtMTkmIzEwOzEzMyAxIDU2IDI3IDY0IDU2IDY0IDIzNCAwIDEwOCA0IDE2MCAxMiAxNjggMTYgMTYgNzAgMTYgODYgMCA5IC05IDEyIC03OSAxMiYjMTA7LTI1NCAwIC0yNzAgMCAtMjcyIC02NSAtMjYwIC0yOSA2IC0zNSAxMSAtMzUgMzEgMCAzMSAtMSAzMSAtNTEgLTIgLTM2IC0yMyYjMTA7LTUxIC0yNyAtMTIyIC0yNyAtNzIgLTEgLTg2IDIgLTExNSAyNCAtNzAgNTIgLTc2IDc0IC04MCAyODMgLTMgMTM3IC0xIDE5MiA4JiMxMDsyMDIgMTUgMTggNzEgMjAgODggM3ogbTExODAgNiBjMTMgLTQgMjIgLTE0IDIyIC0yNSAwIC0yNCAxMSAtMjQgNDMgMSA2MCA0OCYjMTA7MTczIDMyIDIxOSAtMzAgbDIwIC0yOCAzOSAzOCBjMzEgMzAgNTAgNDAgODkgNDUgOTYgMTMgMTM4IC00IDE5NSAtNzkgbDMwJiMxMDstMzkgMyAtMTg5IGM0IC0yMDggMiAtMjE4IC01MiAtMjE4IC01MyAwIC01NiAxMCAtNTYgMTc3IDAgMTU3IC02IDE4OCAtNDQmIzEwOzIzMSAtMjYgMjkgLTkzIDMxIC0xMjYgMiAtNDUgLTM5IC01MCAtNjMgLTUwIC0yMjkgMCAtMTcxIC0zIC0xODEgLTU1IC0xODEmIzEwOy01MiAwIC01NSA5IC01NSAxODcgMCAxNzAgLTUgMTk1IC00OSAyMzEgLTIwIDE2IC02MiAxNSAtODggLTMgLTQ1IC0zMSAtNTMmIzEwOy02NyAtNTMgLTIzNSAwIC0xMDggLTQgLTE2MCAtMTIgLTE2OCAtMTYgLTE2IC03MCAtMTYgLTg2IDAgLTE3IDE3IC0xNyA0ODkgMCYjMTA7NTA2IDEzIDEzIDMxIDE1IDY2IDZ6IG04OTAgLTYgYzE3IC0xNyAxNyAtNDg5IDAgLTUwNiAtMTYgLTE2IC03MCAtMTYgLTg2IDAmIzEwOy0xNyAxNyAtMTcgNDg5IDAgNTA2IDE2IDE2IDcwIDE2IDg2IDB6Ii8+CjxwYXRoIGQ9Ik0yNjQwIDEwNjcgYy0yMSAtNyAtNDUgLTI4IC02MiAtNTIgLTIzIC0zNCAtMjcgLTUwIC0yOCAtMTExIDAgLTk5JiMxMDsyOCAtMTQ5IDk1IC0xNjQgNDUgLTEwIDExMiAzIDEzMyAyNiAzOSA0MiA2OSAxODIgNDMgMTk4IC01IDMgLTEyIDE3IC0xNSAzMiYjMTA7LTkgMzQgLTUzIDc0IC04MiA3NCAtMTIgMCAtMjggMiAtMzYgNCAtNyAzIC0yOSAwIC00OCAtN3oiLz4KPC9nPgo8L3N2Zz4='

      var xs = x_spreadsheet('#x-spreadsheet-demo', {showToolbar: true, showGrid: true,
      showBottomBar: false,
      extendToolbar: {
          left: [
            {
              tip: 'Submit',
              icon: saveIcon,
              onClick: (data, sheet) => {
              console.log('click save button：', data, sheet)
              $('#myModal').show();
              $("#myModalClose").click(function () {
                    $('#myModal').hide();
              });
              $("#errorModalOK").click(function () {
                    $('#errorModal').hide();
              });
              $("#errorModalClose").click(function () {
                    $('#errorModal').hide();
                    /* window.location.assign("/spreadsheet/stockhawk_submission"); */
              });
              $("#myModalOK").off().click(function () {
                    console.log(data);
                    console.log(sheet);
                    $('#myModal').hide();
                    $('#loader1').show();
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
                                    $('#loader1').hide();
                                    window.location.assign("/my/orders/"+data['result']['orderId']+"?access_token="+data['result']['accessToken']);
                                }else{
                                    $('#loader1').hide();
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
            len: 3,
            0: { width: 350 },
            1: { width: 70 },
            2: { width: 100 },
          },
          rows,
        }]).change((cdata));

      setTimeout(() => {
      }, 50000);
    }

